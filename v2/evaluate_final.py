"""
Phase 6 - honest final evaluation.  The TEST set is evaluated exactly once (guarded by data/TEST_TOUCHED).
   python3 v2/evaluate_final.py --set validation          # dry run on VALIDATION (writes results_v2_dryrun_validation.json)
   python3 v2/evaluate_final.py --set test --final         # the one real run (writes results_v2.json + RESULTS.md)
Unit of analysis = scenario (each scenario's 3 seeds are averaged first); all comparisons are paired (identical arrivals).
"""
import os, sys, json, time, argparse
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import harness as H
import fuzzy2

DATA = os.path.join(H.HERE, 'data')
BOOT = 10000
TIE = 0.01                      # |relative difference| < 1% counts as a tie


def boot_ci(x, seed=12345):
    x = np.asarray(x, float)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(x), size=(BOOT, len(x)))
    m = x[idx].mean(axis=1)
    return [float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))]


def select_candidates():
    """Pick optimiser results by VALIDATION score only. Returns {name: spec} and a description of the selection."""
    res = json.load(open(os.path.join(DATA, 'opt_results.json')))
    cands, info = {}, {}
    for struct in sorted({r['struct'] for r in res}):
        rs = [r for r in res if r['struct'] == struct]
        for opt in sorted({r['opt'] for r in rs}):
            best = min((r for r in rs if r['opt'] == opt), key=lambda r: r['val_fitness'])
            name = f"{struct}_{opt}"
            kind = 'fuzzy1' if struct == 'fuzzy1_new' else 'fuzzy2'
            cands[name] = {'type': kind, ('theta' if kind == 'fuzzy1' else 'genes'): best['x']}
            info[name] = {'seed': best['seed'], 'train_fitness': best['train_fitness'], 'val_fitness': best['val_fitness']}
        top = min(rs, key=lambda r: r['val_fitness'])
        info[struct + '_best'] = {'opt': top['opt'], 'seed': top['seed'], 'val_fitness': top['val_fitness']}
    v2 = [k for k in cands if k.startswith('fuzzy2')]
    official = min(v2, key=lambda k: info[k]['val_fitness']) if v2 else None
    return cands, info, official


def all_specs():
    bl = json.load(open(os.path.join(DATA, 'baselines.json')))
    v1 = json.load(open(os.path.join(H.ROOT, 'results.json')))
    specs = {
        'fixed_30s': {'type': 'fixed', 'd': 30},
        'best_fixed_29s': {'type': 'fixed', 'd': bl['fixed']['best_by_normalized']},
        'best_fixed_56s': {'type': 'fixed', 'd': bl['fixed']['best_by_raw_mean']},
        'actuated': {'type': 'actuated', 'gain': bl['actuated']['best_gain_by_normalized']},
        'pressure_split': {'type': 'pressure'},
        'longest_queue_first': {'type': 'lqf'},
        'fuzzy_v1_default': {'type': 'fuzzy1', 'theta': [25.0, 60.0, 35.0]},
        'fuzzy_v1_GA_official': {'type': 'fuzzy1', 'theta': [float(x) for x in v1['best_theta']]},
        'fuzzy_v2_default': {'type': 'fuzzy2', 'genes': list(map(float, fuzzy2.DEFAULT_GENES))},
    }
    cands, info, official = select_candidates()
    specs.update(cands)
    return specs, info, official


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--set', default='validation', choices=['validation', 'test'])
    ap.add_argument('--final', action='store_true')
    ap.add_argument('--force', action='store_true')
    a = ap.parse_args()
    lock = os.path.join(DATA, 'TEST_TOUCHED')
    if a.set == 'test':
        if not a.final:
            sys.exit("refusing to touch TEST without --final")
        if os.path.exists(lock) and not a.force:
            sys.exit("TEST was already evaluated once (data/TEST_TOUCHED); refusing to look again without --force")
        open(lock, 'w').write(time.strftime('%Y-%m-%d %H:%M:%S') + ' test evaluation started\n')
    t0 = time.time()
    specs, info, official_v2 = all_specs()
    set_name = a.set
    keys = ('avg_delay_sec', 'p95_queue', 'max_queue', 'worst_dir_delay_sec', 'served_total', 'total_vehicles')
    raw = {n: H.evaluate(s, set_name, keys) for n, s in specs.items()}
    # unrealisable per-run oracle fixed duration (hindsight), as a headroom reference only
    orc = np.min([H.evaluate({'type': 'fixed', 'd': d}, set_name)['avg_delay_sec'] for d in range(10, 61)], axis=0)
    per = {n: {k: H.per_scenario(v[k], set_name) for k in keys} for n, v in raw.items()}
    per['oracle_fixed_UNREALISABLE'] = {'avg_delay_sec': H.per_scenario(orc, set_name)}
    scn = H.SETS[set_name]
    ref = {r: per[r]['avg_delay_sec'] for r in ('fixed_30s', 'best_fixed_29s', 'best_fixed_56s', 'fuzzy_v1_GA_official', 'actuated')}

    def vs(d, base):          # per-scenario % reduction in avg delay relative to `base`
        return (base - d) / base * 100.0

    out = {'set': set_name, 'n_scenarios': len(scn), 'seeds_per_scenario': [len(s['seeds']) for s in scn][0], 'bootstrap': BOOT,
           'tie_threshold': TIE, 'official_v2_by_validation': official_v2, 'selection_info': info, 'controllers': {}}
    for n in per:
        d = per[n]['avg_delay_sec']
        c = {'spec': specs.get(n), 'mean_avg_delay_s': float(d.mean()), 'median_avg_delay_s': float(np.median(d))}
        for rn, rb in ref.items():
            imp = vs(d, rb)
            ci = boot_ci(imp)
            diff = d - rb
            wl = {'win': int((diff < -TIE * rb).sum()), 'loss': int((diff > TIE * rb).sum())}
            wl['tie'] = len(d) - wl['win'] - wl['loss']
            c['vs_' + rn] = {'mean_pct_improvement': float(imp.mean()), 'ci95': ci, 'median_pct_improvement': float(np.median(imp)), **wl}
        imp30 = vs(d, ref['fixed_30s']); w = int(imp30.argmin())
        c['worst_case_vs_fixed_30s'] = {'scenario': scn[w]['name'], 'pct_improvement': float(imp30[w])}
        if n in raw:
            c['mean_p95_queue'] = float(per[n]['p95_queue'].mean()); c['mean_max_queue'] = float(per[n]['max_queue'].mean())
            c['mean_worst_direction_delay_s'] = float(per[n]['worst_dir_delay_sec'].mean())
            c['mean_throughput_fraction'] = float((per[n]['served_total'] / per[n]['total_vehicles']).mean())
        c['per_scenario_delay_s'] = d.tolist()
        out['controllers'][n] = c
    # by demand profile
    prof = sorted({s['profile'] for s in scn})
    out['by_profile_pct_vs_fixed_30s'] = {n: {p: float(np.mean([vs(per[n]['avg_delay_sec'], ref['fixed_30s'])[i] for i, s in enumerate(scn) if s['profile'] == p])) for p in prof}
                                           for n in ('best_fixed_56s', 'actuated', 'fuzzy_v1_GA_official', 'fuzzy_v2_default', official_v2) if n}
    # decision rule: v2 official vs v1+GA official
    if official_v2:
        dv2, d1 = per[official_v2]['avg_delay_sec'], ref['fuzzy_v1_GA_official']
        diff = (d1 - dv2) / d1 * 100.0
        ci = boot_ci(diff)
        out['decision'] = {'v2_candidate': official_v2, 'mean_pct_reduction_vs_v1_GA': float(diff.mean()), 'ci95': ci,
                           'promote_v2': bool(diff.mean() > 0 and ci[0] > 0),
                           'rule': 'promote v2 only if mean paired reduction vs v1+GA > 0 and the 95% bootstrap CI excludes zero'}
        da = ref['actuated']
        diffa = (da - dv2) / da * 100.0
        out['v2_vs_actuated'] = {'mean_pct_reduction': float(diffa.mean()), 'ci95': boot_ci(diffa)}
    out['legacy_scenarios'] = {}
    out['seconds'] = time.time() - t0
    if a.set == 'test':
        out['legacy_scenarios'] = legacy(specs)
        json.dump(out, open(os.path.join(H.HERE, 'results_v2.json'), 'w'), indent=1)
        cp = os.path.join(DATA, 'controllers.json')
        if os.path.exists(cp) and 'decision' in out:
            with open(cp) as fh:
                cj = json.load(fh)
            cj['promoted'] = out['decision']['promote_v2']
            with open(cp, 'w') as fh:
                json.dump(cj, fh, indent=1)
        open(lock, 'a').write(time.strftime('%Y-%m-%d %H:%M:%S') + ' test evaluation finished\n')
    else:
        out['legacy_scenarios'] = legacy(specs)
        json.dump(out, open(os.path.join(H.HERE, 'results_v2_dryrun_validation.json'), 'w'), indent=1)
    print(f"done in {time.time()-t0:.0f}s; official v2 candidate (by validation): {official_v2}")
    for n, c in out['controllers'].items():
        print(f"{n:<28} mean delay {c['mean_avg_delay_s']:8.1f}s   vs fixed30 {c['vs_fixed_30s']['mean_pct_improvement']:+6.1f}% [{c['vs_fixed_30s']['ci95'][0]:+.1f},{c['vs_fixed_30s']['ci95'][1]:+.1f}]  vs v1GA {c['vs_fuzzy_v1_GA_official']['mean_pct_improvement']:+6.1f}%  vs actuated {c['vs_actuated']['mean_pct_improvement']:+6.1f}%")
    if 'decision' in out:
        print('DECISION', json.dumps(out['decision']))


def legacy(specs):
    """The 5 named v1 scenarios, seed 99 exactly as in the deck (single seed -> no CI)."""
    rows = {}
    for n, s in specs.items():
        d = H.evaluate(s, 'legacy')['avg_delay_sec']
        rows[n] = {sc['name']: float(x) for sc, x in zip(H.SETS['legacy'], d)}
    f = rows['fixed_30s']
    imp = {n: {k: (f[k] - v) / f[k] * 100 for k in f} for n, v in rows.items()}
    held = ('rush_hour', 'heavy')
    return {'avg_delay_s': rows, 'pct_vs_fixed_30s': imp,
            'summary': {n: {'mean_all5': float(np.mean(list(i.values()))), 'mean_held_out(rush_hour,heavy)': float(np.mean([i[k] for k in held])), 'uneven': i['uneven']} for n, i in imp.items()}}


if __name__ == '__main__':
    main()
