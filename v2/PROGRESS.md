# PROGRESS LOG (v2 autonomous build)

Conventions: all commands use `/usr/bin/python3` (3.9.6, numpy 2.0.2, **no matplotlib** -> no charts). 10 CPU cores.

## [setup] Backup + git
- Backup copy: `../traffic_project_backup_1791471006`. `git init`, committed everything, tag `v1-verified`.
- v1 files are frozen; all v2 work lives in `v2/`.
- NOTE on v1 state: `results.json` currently holds the *old* GA run (theta 26.36/28.995/49.378; uneven GA 228.9s) and
  the traces/replays were recorded from it. The *multi-seed* GA run (theta 32.784/30.785/52.154; uneven 217.7s = 57.0%) is in
  `results_multiseed.json`. The brief calls the latter "v1 official", so the baseline file records BOTH and v2 compares against the multi-seed one.

## [phase 0] baseline audit  (see v2/baseline_v1.json, v2/phase0.log)
- Re-ran the v1 GA exactly as `final_comparison.py` does (pop 40, gen 50, seed 1, seeds 7/17/27): theta = [32.784, 30.785, 52.154], matches `results_multiseed.json` (deterministic, 100 s).
- FINDING: `results.json` ALREADY equals the multi-seed result (the user promoted it; traces/replays rebuilt: final cumulative delay 352298.5 / 1618 veh = 217.7 s). The earlier single-seed theta (26.36/28.995/49.378) now exists only in `backup_before_multiseed/results.json`. Baseline file records both; v2 compares against the multi-seed theta (official).
- Legacy 5 scenarios, seed 99: Fixed 506.3 / Fuzzy+GA 217.7 on `uneven` (57.0%). Headline 26.8% = mean of 5 legacy scenarios; 37.9% = mean of the 2 held-out (rush_hour, heavy).
- `phase0_baseline.py` deliberately does not call `final_comparison.main()` (it would overwrite v1's results.json).

## [phase 1] scenarios (v2/scenarios.py -> v2/data/scenarios.json)
- Generator seeds recorded: train 1001, validation 2002, test 3003; 40/20/60 scenarios, 6 profile kinds (+ constant doubled). Disjointness asserted (no identical knot tables; test sim seeds disjoint from train/val sim seeds).
- TRAIN uses sim seeds (7,17,27) per scenario (same as v1 fitness), VALIDATION (101,102,103), TEST 3 fresh seeds per scenario drawn from the test generator RNG.
- Legacy 5 kept separately (seed 99 as in v1).

## [phase 3] simulate2 (v2/simulate2.py)
- Pre-drawn arrivals (bulk `rng.poisson` with interleaved NS/EW lambdas) reproduce v1's scalar-call stream EXACTLY: v1 vs simulate2 on 5 legacy scenarios x seeds {99,7,3} x 4 controllers -> max relative diff in avg delay = 0.0 (bit-identical; tolerance asked was 0.5%).
- Design decision: arrivals are controller-independent, so the same pre-drawn arrays are reused across all controllers/evals (common random numbers => paired comparisons, and ~5x faster fitness).
