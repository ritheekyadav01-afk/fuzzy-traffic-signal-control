"""Records per-second traces of the 'uneven' scenario for replay.html."""
import json
import math
from simulate import run_simulation, fixed_timer_controller
from fuzzy_core import green_duration

NS_RATE, EW_RATE = 0.35, 0.10
DURATION, EVAL_SEED = 3600, 99

with open('results.json') as f:
    res = json.load(f)
theta = res['best_theta']
ref = res['results']['uneven']


def record(ctrl, path):
    trace = []

    def tick(t, qns, qew, phase, cum):
        trace.append({"t": t, "queue_ns": round(qns, 3), "queue_ew": round(qew, 3),
                      "phase": phase, "cumulative_delay": round(cum, 3)})

    out = run_simulation(ctrl, NS_RATE, EW_RATE, duration_seconds=DURATION,
                         seed=EVAL_SEED, on_tick=tick)

    # Recover cumulative departures per direction from the recorded queues (for the 3D
    # replay's drive-off animation). Each second: delta = arrivals - served, arrivals is
    # an integer and served < 1, so arrivals = ceil(delta) and served = arrivals - delta.
    # Cross-checked below: recovered arrivals must sum to the simulator's own total.
    prev = {'ns': 0.0, 'ew': 0.0}
    dep = {'ns': 0.0, 'ew': 0.0}
    arrived = 0
    for row in trace:
        for d in ('ns', 'ew'):
            delta = row['queue_' + d] - prev[d]
            a = math.ceil(delta - 1e-9)
            served = a - delta
            assert a >= 0 and -1e-9 <= served < 1, (row, d)
            assert served < 1e-9 or row['phase'] == d.upper(), (row, d)  # only on green
            arrived += a
            dep[d] += served
            prev[d] = row['queue_' + d]
            row['departed_' + d] = round(dep[d], 3)
    assert arrived == out['total_vehicles'], (arrived, out['total_vehicles'])

    with open(path, 'w') as f:
        json.dump(trace, f)
    return out['avg_delay_sec'], out['total_vehicles']


fixed, nf = record(fixed_timer_controller, 'trace_fixed.json')
fuzzy, ng = record(lambda q, w: green_duration(q, w, theta), 'trace_fuzzy_ga.json')
print(f"Fixed-timer avg delay: {fixed:.1f}s (results.json: {ref['fixed']:.1f}s)")
print(f"Fuzzy+GA   avg delay: {fuzzy:.1f}s (results.json: {ref['fuzzy_ga']:.1f}s)")
print(f"Improvement: {(fixed-fuzzy)/fixed*100:.1f}%  vehicles: {nf}, {ng}")
assert abs(fixed - ref['fixed']) < 0.1 and abs(fuzzy - ref['fuzzy_ga']) < 0.2, "MISMATCH"
print("MATCH")

# inline both traces into a self-contained replay.html (fetch is blocked on file://)
with open('replay_template.html') as f:
    html = f.read()
data = json.dumps({"fixed": json.load(open('trace_fixed.json')),
                   "fuzzy_ga": json.load(open('trace_fuzzy_ga.json'))}, separators=(',', ':'))
with open('replay.html', 'w') as f:
    f.write(html.replace('/*TRACES*/', data))
print("Wrote replay.html")
