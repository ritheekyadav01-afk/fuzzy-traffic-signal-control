"""Extra robustness check (NOT used for any selection or for the decision rule): 24 out-of-distribution constant-demand
scenarios with rates up to 0.55 veh/s per direction (the training/validation/test generators stop at 0.40), fresh seeds."""
import os, sys, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import harness as H
import evaluate_final as E
import scenarios as S

rng = np.random.default_rng(4004)
scn = []
for i in range(24):
    a, b = rng.uniform(0.03, 0.55), rng.uniform(0.03, 0.55)
    s = S.scenario_from_rates(float(a), float(b), name=f'stress_{i:02d}')
    s['seeds'] = [int(x) for x in rng.integers(20_000_000, 90_000_000, size=3)]
    scn.append(s)
H.SETS['stress'] = scn
specs, info, official = E.all_specs()
names = ['fixed_30s', 'best_fixed_56s', 'actuated', 'fuzzy_v1_GA_official', 'fuzzy_v2_default', official]
base = H.per_scenario(H.evaluate(specs['fixed_30s'], 'stress')['avg_delay_sec'], 'stress')
out = {'n': len(scn), 'rates': 'U(0.03,0.55) per direction', 'official_v2': official, 'rows': {}}
for n in names:
    d = H.per_scenario(H.evaluate(specs[n], 'stress')['avg_delay_sec'], 'stress')
    imp = (base - d) / base * 100
    out['rows'][n] = {'mean_delay_s': float(d.mean()), 'mean_pct_vs_fixed30': float(imp.mean()), 'ci95': E.boot_ci(imp), 'min_pct': float(imp.min())}
    print(f"{n:<24} mean delay {d.mean():8.1f}s  vs fixed30 {imp.mean():+6.1f}% [{out['rows'][n]['ci95'][0]:+.1f},{out['rows'][n]['ci95'][1]:+.1f}]  worst {imp.min():+.1f}%")
json.dump(out, open(os.path.join(H.HERE, 'stress_results.json'), 'w'), indent=1)
