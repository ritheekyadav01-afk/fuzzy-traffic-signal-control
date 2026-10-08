import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT); sys.path.insert(0, HERE)
import numpy as np
from simulate import run_simulation, fixed_timer_controller
from fuzzy_core import green_duration
import simulate2, scenarios
th = [32.784, 30.785, 52.154]
ctrls = {'fixed30': fixed_timer_controller, 'fuzzy_default': lambda q, w: green_duration(q, w),
         'fuzzy_ga': lambda q, w: green_duration(q, w, th), 'fixed17': lambda q, w: 17}
worst = 0
for scn in scenarios.legacy_scenarios():
    a, b = scn['knots'][0][1:]
    for seed in (99, 7, 3):
        for name, c in ctrls.items():
            r1 = run_simulation(c, a, b, duration_seconds=3600, seed=seed)
            r2 = simulate2.run_simulation2(c, scn, seed=seed)
            rel = abs(r1['avg_delay_sec'] - r2['avg_delay_sec']) / r1['avg_delay_sec']
            worst = max(worst, rel)
            assert r1['total_vehicles'] == r2['total_vehicles'] and r1['final_queue_ns'] == r2['final_queue_ns']
print('worst relative diff', worst)
