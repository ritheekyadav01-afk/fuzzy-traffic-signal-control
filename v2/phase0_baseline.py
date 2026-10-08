"""Phase 0: re-run the v1 pipeline (read-only wrt v1 files) and freeze v2/baseline_v1.json.
Imports v1 modules from the parent folder; does NOT call final_comparison.main() (it overwrites results.json)."""
import os, sys, json, time
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from simulate import run_simulation, fixed_timer_controller
from fuzzy_core import green_duration, DEFAULT_THETA
import ga_tune

LEGACY = {'light': (0.10, 0.10), 'moderate': (0.20, 0.20), 'uneven': (0.35, 0.10),
          'rush_hour': (0.26, 0.19), 'heavy': (0.30, 0.30)}
HELD_OUT = ('rush_hour', 'heavy')
EVAL_SEED, DURATION = 99, 3600

def fz(theta):
    return lambda q, w: green_duration(q, w, theta)

t0 = time.time()
print("re-running v1 GA exactly as final_comparison.py does (pop=40, gen=50, seed=1, 3-seed fitness)...", flush=True)
theta_rerun, hist = ga_tune.run_ga(pop_size=40, generations=50, seed=1, verbose=False)
print(f"  GA done in {time.time()-t0:.0f}s theta={np.round(theta_rerun,3)} final train fitness={hist[-1]:.3f}s", flush=True)

ms = json.load(open(os.path.join(ROOT, 'results_multiseed.json')))
cur = json.load(open(os.path.join(ROOT, 'results.json')))   # current v1 official (== multiseed)
old = json.load(open(os.path.join(ROOT, 'backup_before_multiseed', 'results.json')))  # earlier single-seed GA run
theta_ms = [float(x) for x in ms['best_theta']]
theta_old = [float(x) for x in old['best_theta']]
match = bool(np.allclose(theta_rerun, theta_ms, atol=5e-4))
print("re-run theta matches results_multiseed.json:", match, flush=True)

def evaluate(ctrl):
    out = {}
    for name, (a, b) in LEGACY.items():
        r = run_simulation(ctrl, a, b, duration_seconds=DURATION, seed=EVAL_SEED)
        out[name] = {'avg_delay_sec': r['avg_delay_sec'], 'total_vehicles': r['total_vehicles']}
    return out

ctrls = {'fixed_30s': fixed_timer_controller,
         'fuzzy_v1_default': fz(DEFAULT_THETA),
         'fuzzy_v1_ga_multiseed(official)': fz(theta_ms),
         'fuzzy_v1_ga_oldrun(earlier single-seed GA, superseded)': fz(theta_old)}
res = {k: evaluate(c) for k, c in ctrls.items()}

def imp(base, x):  # % reduction vs base
    return {n: (res[base][n]['avg_delay_sec'] - res[x][n]['avg_delay_sec']) / res[base][n]['avg_delay_sec'] * 100 for n in LEGACY}
summary = {}
for k in ctrls:
    if k == 'fixed_30s': continue
    im = imp('fixed_30s', k)
    summary[k] = {'improvement_vs_fixed30_pct': im,
                  'mean_all5_pct': float(np.mean(list(im.values()))),
                  'mean_held_out_pct': float(np.mean([im[n] for n in HELD_OUT])),
                  'mean_trained_on_pct': float(np.mean([im[n] for n in LEGACY if n not in HELD_OUT]))}

assert [float(x) for x in cur['best_theta']] == theta_ms, 'results.json is expected to equal results_multiseed.json'
base = {'eval_seed': EVAL_SEED, 'duration_s': DURATION, 'scenarios': {n: list(v) for n, v in LEGACY.items()},
        'held_out_in_v1': list(HELD_OUT),
        'theta_official_multiseed': theta_ms, 'theta_oldrun': theta_old,
        'theta_rerun_this_session': [float(x) for x in theta_rerun], 'rerun_matches_official': match,
        'delays': res, 'summary': summary,
        'notes': ["Headline 26.8% = mean of 5 legacy scenarios (multiseed theta). 37.9% = mean of the 2 held-out (rush_hour, heavy). 57.0% = uneven only.",
                  "results.json == results_multiseed.json == official v1 (user promoted it; traces/replays were rebuilt from it: final fuzzy+GA cumulative delay 352298.5 / 1618 veh = 217.7 s). Earlier quoted 27.8% = mean of 5 scenarios with the OLD single-seed theta; 32.5% came from an earlier 9-scenario draft not reproducible from files in this folder."]}
json.dump(base, open(os.path.join(HERE, 'baseline_v1.json'), 'w'), indent=2)
print(json.dumps({k: {n: round(v['avg_delay_sec'], 1) for n, v in d.items()} for k, d in res.items()}, indent=1))
for k, v in summary.items(): print(k, {kk: (round(vv, 1) if isinstance(vv, float) else None) for kk, vv in v.items() if kk != 'improvement_vs_fixed30_pct'})
