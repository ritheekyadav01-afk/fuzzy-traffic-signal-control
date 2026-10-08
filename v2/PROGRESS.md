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

## [phase 2] baselines (v2/phase2_baselines.py -> v2/data/baselines.json), chosen on TRAIN only
- Best fixed duration: 29 s by the *normalised* criterion (mean delay relative to the per-run best fixed duration), 56 s by the *raw mean delay* criterion. The two criteria disagree because raw mean is dominated by over-saturated scenarios. Both are kept as baselines ("best_fixed_29", "best_fixed_56"); fixed-30 (the deck baseline) is essentially the normalised optimum.
- Actuated rule (green = gain x own queue, clipped 10-60): best gain 3.0 (normalised) / 2.5 (raw).
- Also added: pressure_split (max-pressure style: 70 s budget split by queue share) and longest_queue_first (bang-bang). All conform to controller_fn(queue, waiting[, opposing]).
- **FINDING (important, unflattering to v1):** on TRAIN/VAL the trivial actuated rule gives delay ratio 0.42 / 0.52 relative to best-fixed, vs 0.66 / 0.71 for v1 fuzzy+GA. v1's controller is clearly better than fixed timing but clearly WORSE than a one-line actuated rule. The v2 comparison must therefore be reported against actuated, not only against fixed-30.

## [phase 4] fuzzy-v2 (v2/fuzzy2.py, rules in v2/rules.txt)
- 3 inputs (own queue 0-60, wait 0-120, opposing queue 0-60), 27 rules, 3-breakpoint Ruspini partitions (12 genes) + optional 27 rule weights. `repair()` makes every gene vector a valid partition.
- DECISION: output universe widened to [0,80] and clamped to 10-60 by the simulator: with the v1-style [10,60] universe the centroid of clipped sets can hardly reach 60 s, which handicapped saturated demand. Default (hand-set) fuzzy-v2 scores 0.53 TRAIN ratio vs 0.70 for v1 default (same data), i.e. the opposing-queue input + wider universe already help before any training.
- v1 controller kept intact as fuzzy-v1 (`controllers.fuzzy_v1` reuses v1's own membership code, only caching output shapes; verified identical in tests).

## [phase 5] optimizers (v2/optimizers.py, v2/run_optimizers.py -> v2/data/opt_results.json, v2/optimizers.log)
- GA, PSO, SA, same fitness, same budget (2000 evals each), 3 seeds each, 3 structures: fuzzy2_bp (12 genes), fuzzy2_bpw (39 genes), fuzzy1_new (v1's 3-centre controller re-trained on the new TRAIN set).
- FITNESS CHOICE: mean over TRAIN (scenario, seed) of delay / delay(best fixed 29 s). Reason: raw mean delay is dominated by over-saturated scenarios (v1 weakness: it traded light-traffic performance for heavy). A ratio treats a 5% change on a 13 s scenario like a 5% change on a 500 s scenario. Common random numbers: all controllers see the identical arrivals.
- Every optimizer gets the hand-designed default as one starting candidate (GA ind 0, PSO particle 0, SA start).
- Final theta per structure = best VALIDATION score among its 9 runs. TEST untouched until `evaluate_final.py --final`.

## [phase 7 part] prototype pieces written while optimizers run
- `v2/predict.py` (CLI, rules fired), `v2/server.py` (stdlib http.server; real Python sim, v1 3D viewer fed server-side), `v2/registry.py`, `v2/tests/test_all.py` (22 tests).
- Server smoke test: /healthz, /api/predict, /replay (1.6 MB page, 0 external script tags), POST /api/simulate, bad controller -> HTTP 400.
- Test finding: fuzzy-v2 default is monotone only to within 1 s: 27 sub-second violations (max 0.93 s) out of 2048 grid checks, caused by centroid blending. Test tolerance set to 1 s and the caveat documented rather than hidden.
- Sanity number: actuated rule on legacy `uneven` seed 99 = 49.2 s vs fixed-30 506.3 s (90.3%), v1 fuzzy+GA = 217.7 s (57.0%). Confirms the Phase-2 finding.

## [tooling] written while optimizers run (20:28-20:50 IST)
- `evaluate_final.py` (guarded: TEST needs `--final`, lock file `data/TEST_TOUCHED`), `make_report.py`, `analyze_optimizers.py`, `export_controllers.py`, `build_v2_replays.py`, `run_all.py`, `README.md`, `requirements.txt`.

## [phase 5 result] 27 optimizer runs finished (20:28-22:15 IST, ~40 min/run on contended cores) -> data/opt_results.json, data/optimizer_table.md
- All three structures converge to the same plateau regardless of optimizer: fuzzy-v2 (12 genes) train fitness 0.414-0.419, fuzzy-v2+weights (39 genes) 0.414-0.418, v1 structure RE-TRAINED on the new data 0.639 (v1 official: 0.660 on this TRAIN set).
  => the gain is from the controller STRUCTURE (opposing-queue input, wider output universe), not from more data / more optimisation: re-training v1's 3-centre controller on 40 scenarios gives 0.639 train / 0.70-0.71 val, i.e. almost no better than the original v1 theta.
- Optimizer ranking is not decisive: GA reached the best mean train fitness for fuzzy2_bp (0.4143 +- 0.0019), PSO for fuzzy2_bpw (0.4139) and PSO had the best single run (0.4119). Differences between optimizers (<=0.005) are about the size of seed-to-seed spread. Fastest to 95% of improvement: PSO (590 evals) < GA (637) < SA (723) on fuzzy2_bp.
- Weighted rules (39 genes) did NOT help beyond 12 breakpoints (val 0.510-0.521 vs 0.508-0.515); slower convergence (790-1183 evals). Parsimony wins.
- Selected by VALIDATION: fuzzy2_bp_PSO (seed 2), val 0.5079. Margin over the next candidates is ~0.001-0.002 = noise; selection is nominal, not a real discovery.
- Monotonicity of trained controllers (tolerance 1 s, 1024 grid checks each way): GA 3/0, PSO 0/6, SA 0/18, bpw-GA 0/0, bpw-PSO 0/0, bpw-SA 0/11 violations (own-queue / opposing-queue). Default: 0/0. Trained controllers are mostly monotone but not guaranteed to be.
- Validation dry run (not the official numbers): fuzzy2_bp_PSO vs actuated +3.5% [+0.5,+7.0]; vs v1+GA +32.7% [+22.7,+43.4].
--- FINAL TEST RUN Thu Oct  8 22:16:25 IST 2026 ---

## [phase 6] FINAL TEST EVALUATION (22:16 IST, once; data/TEST_TOUCHED) -> results_v2.json, RESULTS.md
- Official v2 candidate (validation-selected): fuzzy2_bp_PSO. TEST-60: mean delay 71.9 s vs fixed-30 173.5 s (+58.5% [51.7, 65.1]), vs v1 fuzzy+GA +42.4% [36.2, 48.5] (59 W / 0 L / 1 T) -> DECISION RULE CLEARED, v2 promoted.
- Equally important: actuated rule = 74.6 s (+57.8% vs fixed-30); v2 beats it by +4.3% [2.4, 6.5] (31 W / 14 L / 15 T). v1 fuzzy+GA = 105.9 s (+34.9%) is much WORSE than the trivial actuated rule.
- LEGACY-5 (seed 99): v2 mean-of-5 +47.7%, held-out +46.7%, uneven 39.0 s (+92.3%); v1: 26.8 / 37.9 / 57.0 (reproduced exactly).
- Stress set (extra; rates to 0.55): v2 +33.1%, actuated +32.0%, v1+GA +20.5% vs fixed-30.

## [phase 7/8] wrap-up
- server/predict verified (curl + unit tests + headless screenshot of v2 replay). 23 unit tests pass. `run_all.py --quick` reproduced baseline_v1.json and scenarios.json byte-for-byte; only timing fields differ.
- v2 replays regenerated into v2/ (replay_3d_v2.html, trace_*_v2.json) because v2 was promoted; v1 files untouched (git diff vs v1-verified is empty outside v2/).
- Decisions worth re-reading: (1) widened fuzzy output universe to 0-80 (clamped by the sim); (2) normalised fitness vs best-fixed 29 s; (3) tie threshold 1%; (4) stress set generated after the TEST run, used for nothing.
- NOT done: full optimizer re-run end-to-end a second time; real-time visual playback of web/3D; any edit to the PowerPoint decks.
