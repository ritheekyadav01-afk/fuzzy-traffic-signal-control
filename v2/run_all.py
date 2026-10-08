#!/usr/bin/env python3
"""Reproduce everything from fixed seeds.
   /usr/bin/python3 v2/run_all.py            full pipeline (~1-1.5 h on 10 cores: optimizers dominate)
   /usr/bin/python3 v2/run_all.py --quick    reuse saved optimizer results (data/opt_results.json), re-run everything else (~5 min)
   --redo-test   allow a second look at the TEST set (deletes the lock; do NOT do this to tune anything)"""
import os, sys, subprocess, time
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
PY = sys.executable
quick = '--quick' in sys.argv; redo = '--redo-test' in sys.argv


def step(title, cmd):
    t = time.time(); print(f"\n=== {title} ===", flush=True)
    r = subprocess.run([PY] + cmd, cwd=ROOT)
    print(f"--- {title}: exit {r.returncode} ({time.time()-t:.0f}s)", flush=True)
    if r.returncode != 0:
        sys.exit(f"step failed: {title}")


lock = os.path.join(HERE, 'data', 'TEST_TOUCHED')
step('scenarios (fixed seeds)', ['v2/scenarios.py'])
step('phase 0: re-run v1 + baseline_v1.json', ['v2/phase0_baseline.py'])
step('phase 2: baselines on TRAIN', ['v2/phase2_baselines.py'])
if quick and os.path.exists(os.path.join(HERE, 'data', 'opt_results.json')):
    print('\n(quick) reusing data/opt_results.json')
else:
    if os.path.exists(os.path.join(HERE, 'data', 'opt_results.json')):
        os.remove(os.path.join(HERE, 'data', 'opt_results.json'))
    step('phase 5: GA/PSO/SA x 3 structures x 3 seeds', ['v2/run_optimizers.py'])
step('optimizer analysis', ['v2/analyze_optimizers.py'])
step('export validation-selected controllers', ['v2/export_controllers.py'])
step('fuzzy-v2 rules', ['v2/fuzzy2.py'])
step('unit tests', ['-W', 'ignore', '-m', 'unittest', 'discover', '-s', 'v2/tests'])
step('validation dry run', ['v2/evaluate_final.py', '--set', 'validation'])
if os.path.exists(lock) and not redo:
    print('\nTEST already evaluated once (data/TEST_TOUCHED): keeping results_v2.json. Use --redo-test to repeat.')
else:
    if redo and os.path.exists(lock):
        os.remove(lock)
    step('FINAL: test set, evaluated once', ['v2/evaluate_final.py', '--set', 'test', '--final'])
step('RESULTS.md', ['v2/make_report.py'])
import json
cj = json.load(open(os.path.join(HERE, 'data', 'controllers.json')))
if cj.get('promoted'):
    step('v2 replays (promoted)', ['v2/build_v2_replays.py'])
else:
    print('\nfuzzy-v2 not promoted -> v1 remains official; no v2 replays generated.')
print('\nALL DONE')
