"""Render RESULTS.md from results_v2.json (single source of truth) + optimizer tables.   --dry renders the validation dry run instead."""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__))
dry = '--dry' in sys.argv
src = os.path.join(HERE, 'results_v2_dryrun_validation.json' if dry else 'results_v2.json')
R = json.load(open(src)); B = json.load(open(os.path.join(HERE, 'baseline_v1.json')))
dst = os.path.join(HERE, 'RESULTS_DRYRUN_VALIDATION.md' if dry else 'RESULTS.md')
C = R['controllers']
ORDER = [n for n in ['fixed_30s', 'best_fixed_29s', 'best_fixed_56s', 'actuated', 'pressure_split', 'longest_queue_first', 'fuzzy_v1_default', 'fuzzy_v1_GA_official']
         if n in C] + sorted(n for n in C if n.startswith('fuzzy1_new')) + (['fuzzy_v2_default'] if 'fuzzy_v2_default' in C else []) + sorted(n for n in C if n.startswith('fuzzy2_')) + ['oracle_fixed_UNREALISABLE']
ORDER = [n for n in ORDER if n in C]
f1 = lambda x: f"{x:+.1f}"
ci = lambda d: f"{d['mean_pct_improvement']:+.1f}% [{d['ci95'][0]:+.1f}, {d['ci95'][1]:+.1f}]"
wl = lambda d: f"{d['win']}/{d['loss']}/{d['tie']}"
L = []
L.append(f"# RESULTS ({'VALIDATION DRY RUN - not the official numbers' if dry else 'official: TEST set, evaluated once'})\n")
L.append(f"Set: **{R['set']}**, {R['n_scenarios']} scenarios x {R['seeds_per_scenario']} traffic seeds (seeds are averaged inside a scenario; the scenario is the unit of analysis). "
         f"All controllers see identical pre-drawn arrivals (paired). CIs = 95% bootstrap ({R['bootstrap']} resamples over scenarios) of the mean per-scenario % delay reduction. "
         f"Win/loss/tie = scenarios where delay is lower / higher / within {R['tie_threshold']*100:.0f}% of the reference.\n")
L.append("Official fuzzy-v2 candidate (chosen by VALIDATION score only): `%s`\n" % R['official_v2_by_validation'])
L.append("## Table A - all controllers\n")
L.append("| controller | mean delay (s) | vs fixed-30 | vs best-fixed-29 | vs v1 fuzzy+GA | vs actuated | W/L/T vs fixed-30 | W/L/T vs v1+GA | worst case vs fixed-30 | mean p95 queue | worst-dir delay (s) | served/arrived |")
L.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
for n in ORDER:
    c = C[n]; star = ' **(official v2 candidate)**' if n == R['official_v2_by_validation'] else ''
    wc = c['worst_case_vs_fixed_30s']
    L.append(f"| {n}{star} | {c['mean_avg_delay_s']:.1f} | {ci(c['vs_fixed_30s'])} | {ci(c['vs_best_fixed_29s'])} | {ci(c['vs_fuzzy_v1_GA_official'])} | {ci(c['vs_actuated'])} | {wl(c['vs_fixed_30s'])} | {wl(c['vs_fuzzy_v1_GA_official'])} | "
             f"{wc['pct_improvement']:+.1f}% ({wc['scenario']}) | {c.get('mean_p95_queue', float('nan')):.1f} | {c.get('mean_worst_direction_delay_s', float('nan')):.1f} | {c.get('mean_throughput_fraction', float('nan')):.3f} |")
L.append("\n`oracle_fixed_UNREALISABLE` picks the best fixed duration with hindsight on each run: a headroom reference, not a deployable controller.\n")
L.append("Also vs the best fixed timer chosen by raw mean delay (56 s):\n")
L.append("| controller | vs best-fixed-56 | W/L/T |\n|---|---|---|")
for n in ORDER:
    L.append(f"| {n} | {ci(C[n]['vs_best_fixed_56s'])} | {wl(C[n]['vs_best_fixed_56s'])} |")
if 'decision' in R:
    d = R['decision']; v = R['v2_vs_actuated']
    L.append("\n## Decision rule\n")
    L.append(f"- Rule: {d['rule']}.")
    L.append(f"- fuzzy-v2 candidate `{d['v2_candidate']}` vs v1 fuzzy+GA: mean paired reduction **{d['mean_pct_reduction_vs_v1_GA']:+.1f}%**, 95% CI [{d['ci95'][0]:+.1f}, {d['ci95'][1]:+.1f}] -> **promote v2: {d['promote_v2']}**.")
    L.append(f"- Same candidate vs the simple actuated rule: mean paired reduction {v['mean_pct_reduction']:+.1f}%, 95% CI [{v['ci95'][0]:+.1f}, {v['ci95'][1]:+.1f}] (positive = fuzzy-v2 better).")
L.append("\n## Table B - by demand profile (mean % delay reduction vs fixed-30)\n")
profs = sorted(next(iter(R['by_profile_pct_vs_fixed_30s'].values())))
L.append("| controller | " + " | ".join(profs) + " |\n|---|" + "---|" * len(profs))
for n, d in R['by_profile_pct_vs_fixed_30s'].items():
    L.append(f"| {n} | " + " | ".join(f"{d[p]:+.1f}%" for p in profs) + " |")
lg = R['legacy_scenarios']
L.append("\n## Table C - the 5 legacy (v1/deck) scenarios, seed 99 (single seed, no CI)\n")
names = list(next(iter(lg['avg_delay_s'].values())))
L.append("| controller | " + " | ".join(names) + " | mean of 5 | mean of held-out (rush_hour, heavy) |\n|---|" + "---|" * (len(names) + 2))
for n in ORDER:
    if n not in lg['avg_delay_s']: continue
    d, p, s = lg['avg_delay_s'][n], lg['pct_vs_fixed_30s'][n], lg['summary'][n]
    L.append(f"| {n} | " + " | ".join(f"{d[k]:.1f}s ({p[k]:+.1f}%)" for k in names) + f" | {s['mean_all5']:+.1f}% | {s['mean_held_out(rush_hour,heavy)']:+.1f}% |")
L.append("\nv1 reference (baseline_v1.json): v1 fuzzy+GA = " + ", ".join(f"{k} {v['avg_delay_sec']:.1f}s" for k, v in B['delays']['fuzzy_v1_ga_multiseed(official)'].items()) +
         f"; mean of 5 = {B['summary']['fuzzy_v1_ga_multiseed(official)']['mean_all5_pct']:.1f}%, held-out mean = {B['summary']['fuzzy_v1_ga_multiseed(official)']['mean_held_out_pct']:.1f}%.")
tp = os.path.join(HERE, 'data', 'optimizer_table.md')
if os.path.exists(tp) and not dry:
    L.append("\n## Table D - optimizers (same fitness, 2000 evals each, 3 seeds)\n")
    L.append("Fitness = mean over TRAIN (scenario,seed) of delay / delay(best fixed 29 s); lower is better; <1 beats best-fixed.\n")
    L.append(open(tp).read())
open(dst, 'w').write("\n".join(L) + "\n")
print('wrote', dst)
