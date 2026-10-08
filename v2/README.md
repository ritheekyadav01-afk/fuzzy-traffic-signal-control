# Traffic signal control v2 — fuzzy logic + GA / PSO / SA, with an honest evaluation

v2 lives entirely in this folder; the v1 files one level up are untouched (tag `v1-verified`).
Only `numpy` is needed. Use `/usr/bin/python3` (3.9) — the default `python3` on this machine has no numpy.
Everything below is run **from the project root** (`traffic_project_code/`).

## Open the prototype

```bash
/usr/bin/python3 v2/server.py            # then open http://localhost:8000   (stop with Ctrl+C)
/usr/bin/python3 v2/server.py --port 8123
```
Pick a preset or demand profile, rates, seed and controller → the **Python** simulator runs server-side and the 3D replay
opens (fixed-30 s vs your controller; the toggle switches controllers at the same simulated second). No traffic maths runs in
JavaScript. Works offline (Three.js is vendored in `vendor/`). Other endpoints: `/api/predict?queue=30&wait=60&opp=8`,
`/api/controllers`, `POST /api/simulate` (JSON `{"preset":"uneven","seed":99,"controller":"actuated"}`).

## Explainable single decision (CLI)

```bash
/usr/bin/python3 v2/predict.py --queue 30 --wait 60 --opp 8        # trained fuzzy-v2
/usr/bin/python3 v2/predict.py --queue 30 --wait 60 --opp 8 --controller v2-default --json
```

## Tests

```bash
/usr/bin/python3 -W ignore -m unittest discover -s v2/tests -v
```

## Reproduce everything from fixed seeds

```bash
/usr/bin/python3 v2/run_all.py --quick     # reuse saved optimizer runs (~5 min)
/usr/bin/python3 v2/run_all.py             # full, including 27 optimizer runs (~1 h on 10 cores)
```
The TEST set is evaluated once; `data/TEST_TOUCHED` records that and the script refuses a second look unless `--redo-test`.

## Layout

| file | role |
|---|---|
| `scenarios.py`, `data/scenarios.json` | generator (6 demand profiles) + TRAIN 40 / VALIDATION 20 / TEST 60 + 5 legacy, fixed seeds |
| `simulate2.py` | v1 model + time-varying demand, per-direction delay, p95/max queue, throughput, fairness, trace hook; bit-identical to v1 on constant demand |
| `controllers.py`, `fuzzy2.py`, `rules.txt` | baselines (fixed, best-fixed, actuated, pressure-split, longest-queue-first), fuzzy-v1, fuzzy-v2 (27 rules) |
| `optimizers.py`, `run_optimizers.py`, `analyze_optimizers.py` | GA, PSO, SA with identical fitness and budget |
| `evaluate_final.py`, `make_report.py` | paired evaluation, bootstrap CIs, decision rule → `results_v2.json`, `RESULTS.md` |
| `predict.py`, `server.py`, `registry.py` | functional prototype |
| `baseline_v1.json` | frozen v1 numbers every comparison refers to |
| `FINAL_REPORT.md`, `DECK_NUMBERS.md`, `PROGRESS.md` | write-up, slide numbers, timestamped build log |
