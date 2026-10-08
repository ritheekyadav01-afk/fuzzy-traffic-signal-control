# FINAL REPORT — v2 of the fuzzy + evolutionary traffic-signal controller

Everything below was produced by code in `v2/` and every number is copied from files that the code wrote
(`results_v2.json`, `baseline_v1.json`, `data/opt_results.json`, `stress_results.json`; tables in `RESULTS.md`, `DECK_NUMBERS.md`).
v1 is untouched (`git diff v1-verified -- . ':!v2'` is empty; tag `v1-verified`, plus a copy in `../traffic_project_backup_1791471006`).

## 1. Verdict in four sentences

1. **v2 clears the pre-registered promotion rule**: on the 60-scenario TEST set it reduces delay vs v1 fuzzy+GA by **42.4 %** (95 % CI 36.2 – 48.5, wins in 59 of 60 scenarios, 1 tie), so v2 is the official system.
2. **But the biggest finding is about v1, not v2**: a one-line actuated rule (green = 3 s × own queue, clipped to 10–60 s) already reduces delay vs fixed-30 by **57.8 %** on TEST, far more than v1 fuzzy+GA (**34.9 %**). v1's fuzzy+GA beat the *fixed timer* it was compared against, but it is clearly worse than a trivial adaptive baseline that nobody had tried.
3. **fuzzy-v2 beats that actuated rule, narrowly**: +4.3 % (95 % CI +2.4 to +6.5; 31 wins / 14 losses / 15 ties at a 1 % tie threshold). Statistically positive, practically small. What fuzzy-v2 really adds over the actuated rule is explainability (rules fired), a smoother treatment of the opposing queue and slightly better fairness/queues — not a different league of delay.
4. **The training data and the optimizer mattered much less than the controller structure**: re-training v1's 3-parameter controller on 40 new scenarios with three different optimizers barely moved it (TRAIN fitness 0.639 vs 0.660 for v1's official theta), whereas giving the controller the opposing queue and a wider output universe took it to ≈0.414.

## 2. What was built (phases)

| phase | deliverable | result |
|---|---|---|
| 0 baseline audit | `baseline_v1.json`, `phase0_baseline.py` | v1 GA re-run reproduces theta [32.784, 30.785, 52.154] exactly; uneven seed 99: fixed 506.3 s, fuzzy+GA 217.7 s (57.0 %). LEGACY-5 mean 26.8 %, held-out pair 37.9 %. |
| 1 data | `scenarios.py`, `data/scenarios.json` | 6 demand profiles (constant, rush ramp, surge, one-sided surge, lull, balanced-then-skewed). TRAIN 40 / VALIDATION 20 / TEST 60 (+5 legacy). Fixed generator seeds 1001/2002/3003; disjointness asserted in code and in a test. |
| 2 baselines | `controllers.py`, `phase2_baselines.py` | fixed-30, best fixed 29 s (normalised criterion) and 56 s (raw-mean criterion), actuated (gain 3.0), pressure-split, longest-queue-first — all tuned on TRAIN only. |
| 3 simulator | `simulate2.py` | time-varying demand, per-direction delay, p95/max queue, throughput, worst-direction delay, `on_tick`/trace hook, opposing-queue argument. **Bit-identical to v1** on constant demand (max relative difference 0.0, 5 scenarios × 3 seeds × 4 controllers; requested tolerance was 0.5 %). |
| 4 controller | `fuzzy2.py`, `rules.txt` | 3 inputs (own queue, waiting time, opposing queue), 27 readable rules, 12 ordered breakpoints (+27 optional rule weights); `repair()` makes every gene vector a valid partition. v1 controller retained as fuzzy-v1. |
| 5 optimizers | `optimizers.py`, `run_optimizers.py` | GA, PSO, SA; same fitness; 2000 evaluations each; 3 seeds; 3 structures = 27 runs (~40 min each on contended cores). Final theta chosen on VALIDATION. |
| 6 evaluation | `evaluate_final.py` → `results_v2.json`, `RESULTS.md` | TEST evaluated once (lock file); paired comparisons; bootstrap CIs; W/L/T; worst case; p95 queue; fairness. |
| 7 prototype | `predict.py`, `server.py`, `run_all.py`, `tests/` | CLI with rules fired; stdlib web app that runs the real Python simulation and feeds the 3D replay; one-command reproduction; 23 unit tests, all passing. |

## 3. Headline numbers (TEST-60 unless stated; mean over scenarios, 3 fresh seeds each, paired)

| controller | mean delay | reduction vs fixed-30 (95 % CI) | vs v1 fuzzy+GA | vs actuated |
|---|---|---|---|---|
| fixed-30 | 173.5 s | — | — | — |
| best fixed 56 s (raw-mean optimum) | 160.4 s | −6.9 % (−13.9, −0.6) | | |
| actuated (gain 3.0) | 74.6 s | +57.8 % (+51.3, +64.2) | +40.7 % | — |
| fuzzy-v1 default | 121.8 s | +29.4 % (+24.8, +34.3) | −11.2 % | |
| **fuzzy-v1 + GA (v1 official)** | 105.9 s | +34.9 % (+29.6, +40.3) | — | −106 % |
| fuzzy-v2 default (hand-set) | 85.4 s | +47.8 % (+41.4, +54.1) | +23.3 % | −41 % |
| **fuzzy-v2 + PSO (official v2)** | **71.9 s** | **+58.5 % (+51.7, +65.1)** | **+42.4 % (+36.2, +48.5)** | **+4.3 % (+2.4, +6.5)** |

Other TEST-60 metrics (official v2 / actuated / v1+GA / fixed-30): mean p95 queue 80.3 / 82.9 / 108.8 / 168.8 vehicles; worst-direction mean delay 82.8 / 88.0 / 126.9 / 223.5 s; served-over-arrived 0.971 / 0.969 / 0.953 / 0.910. Worst single scenario for v2 vs fixed-30 is still +6.3 % (test_43_constant): v2 never lost to fixed-30 (60 wins, 0 losses, 0 ties); v1+GA also never lost (60/0/0) but its worst case is only +5.0 %.

**LEGACY-5 (the deck's scenarios, seed 99, single seed so no CI):** v2 gives uneven 39.0 s (+92.3 %), rush_hour 40.1 s, heavy 398.7 s; mean of 5 = **+47.7 %**, held-out pair = **+46.7 %**, vs 26.8 % / 37.9 % / 57.0 % for v1. The actuated rule gets +47.3 % / +46.0 % / +90.3 % on the same scenarios — i.e. essentially the same as v2.

**Where each controller is strong (TEST-60, % vs fixed-30):** v2 and actuated are within ~2 points on every profile (balanced-then-skewed +84.8 vs +83.0; one-sided surge +75.3 vs +74.0; lull +41.6 vs +42.5; surge +42.0 vs +42.6). v1+GA is weakest on lull (+11.3 %) and surge (+22.2 %). The raw-mean-optimal fixed timer (56 s) is a trap: −56.9 % on lull, −15.9 % on surge.

**Robustness beyond the training range** (extra, post-hoc, used for no decision; 24 constant-demand scenarios with rates up to 0.55 veh/s): fixed-30 552.8 s; v1+GA +20.5 %; actuated +32.0 %; fuzzy-v2 default +27.4 %; **official v2 +33.1 %** (CIs overlap with actuated). Everything degrades in over-saturation; nothing breaks.

## 4. Optimizers (Phase 5; fitness = mean delay relative to best-fixed on TRAIN, lower is better)

| structure | GA | PSO | SA |
|---|---|---|---|
| fuzzy-v2, 12 genes: TRAIN (mean ± sd, 3 seeds) | 0.4143 ± 0.0019 | 0.4186 ± 0.0047 | 0.4189 ± 0.0017 |
| fuzzy-v2, 12 genes: VALIDATION mean | 0.5103 | 0.5156 | 0.5151 |
| fuzzy-v2 + rule weights, 39 genes: TRAIN | 0.4157 ± 0.0014 | 0.4139 ± 0.0010 | 0.4183 ± 0.0050 |
| fuzzy-v1 structure re-trained on new TRAIN: TRAIN | 0.6391 ± 0.0001 | 0.6392 ± 0.0008 | 0.6395 ± 0.0002 |

* Evaluations to reach 95 % of the final improvement (12-gene structure): PSO 590, GA 637, SA 723 — PSO converged fastest, SA slowest, but all reach the same plateau.
* Best single run: PSO seed 2 (TRAIN 0.4119, VALIDATION 0.5079) → official v2. Its VALIDATION margin over the other candidates is ≈ 0.001–0.002, which is noise; **the selection is nominal, not a discovery**. All six fuzzy-v2 candidates evaluated on TEST would have passed the decision rule (`RESULTS.md`, Table A: +40.9 % to +42.4 % vs v1+GA, every CI lower bound above +34 %); against the actuated rule they range from −0.0 % (12-gene SA) to +4.4 % (39-gene PSO).
* The 27 rule weights did **not** help (0.414–0.418 vs 0.414–0.419) and converged more slowly (790–1183 evaluations). Parsimony wins.
* Trained controllers are mostly but not perfectly monotone (tolerance 1 s, 1024 grid checks each direction): GA 3/0, PSO 0/6, SA 0/18 violations (own-queue / opposing-queue); the hand-set default has 0/0. All violations are sub-second-to-few-second centroid effects.

What the trained controller learned (official genes, real units): own queue becomes "high" from ≈23 vehicles and "medium" peaks at 9; opposing queue "high" from ≈22; the green output sets sit at (15, 24, 50) s. The waiting-time breakpoints moved to 71–104 s, so the waiting input rarely fires — the optimizer effectively relied on the two queues, consistent with the actuated rule doing as well.

## 5. Fitness-function choice (and its consequence)

v1's fitness (mean raw delay) is dominated by heavy scenarios, which is why v1+GA traded light-traffic performance for heavy-traffic gains. v2 normalises each (scenario, seed) delay by the best-fixed-timer delay on the same run, so a 5 % change counts equally everywhere. Consequence: v2 does not sacrifice light traffic (legacy `light` 8.2 s vs 13.3 s fixed; v1+GA 13.3 s = no gain).

## 6. What did NOT improve / what failed or was only partly done

* **v2 is not a breakthrough over the simple actuated rule** (+4.3 %). If the claim is "adaptive control matters", the evidence is overwhelming; if the claim is "fuzzy + evolutionary optimisation is needed", the evidence says a one-parameter rule gets 99 % of the way.
* **Optimizer choice made no practical difference.** GA, PSO and SA end within the seed-to-seed spread of each other.
* **Rule weights (39 genes) gave no gain.**
* **v1 retraining gave no gain** (0.639 vs 0.660 TRAIN): the v1 structure (own queue 0–50 only, output universe 10–60) is the limit.
* **Over-saturated scenarios** (e.g. legacy `heavy`, 0.30 + 0.30 veh/s exceeds the ≈0.45 veh/s capacity of this 2-phase model): every controller ends at 396–466 s; the metric there measures how large a queue has built up in one hour, not control quality.
* **Not done / not verified:** (a) the full 27-run optimizer sweep was run once; `run_all.py --quick` re-ran every other stage from fixed seeds and reproduced `baseline_v1.json` and `scenarios.json` byte-for-byte, but I did not repeat the 1-hour optimizer sweep itself (each run is deterministic by seed and a unit test checks that on a toy function, but that is not a full end-to-end re-run); (b) the web app and the 3D page were checked with `curl`, unit tests and headless screenshots — nobody watched a real-time playback in a visible browser; (c) the existing decks and the v1 replays were deliberately not edited.
* **Process note:** the 'official' v2 candidate was picked from 18 candidates on VALIDATION; the TEST set was evaluated exactly once (`data/TEST_TOUCHED` has the timestamps 22:16:25 → 22:16:52). The stress set was generated after the TEST evaluation but is independent of every choice made.

## 7. Limitations (say these before the examiner does)

* **Synthetic data only.** Arrivals are Poisson with piecewise-linear rates; no real detector data, no platoons, turning movements, pedestrians, yellow/all-red variation, or lane-level queues.
* **Two-phase, single intersection, strictly alternating phases.** The controller chooses only the duration of the next green (10–60 s); it cannot skip a phase, so "max-pressure" here is a loose analogue.
* **Delay metric:** sum of queued vehicles per second ÷ vehicles that arrived in the hour. Vehicles still queued at 3600 s contribute only their waiting so far, so over-saturated scenarios are horizon-dependent. It is the same definition v1 used (reproduced exactly).
* **Statistics:** CIs are bootstrap over scenarios drawn from *my* generator; they say the result is stable across that scenario distribution, not that it transfers to real roads. Ties use a 1 % threshold chosen before looking at TEST. The 60 test scenarios share generator structure with TRAIN/VALIDATION.
* **Controller inputs are idealised:** exact queue counts, no sensor noise.
* **Centroid defuzzification** produces small non-monotonicities (≤ 1 s for the default; a few more seconds for some trained controllers).

## 8. Reproduce

```bash
/usr/bin/python3 -W ignore -m unittest discover -s v2/tests -v     # 23 tests
/usr/bin/python3 v2/run_all.py --quick                              # everything except the 1 h optimizer sweep (~5 min); TEST is NOT re-opened
/usr/bin/python3 v2/run_all.py                                      # everything (≈1–1.5 h)
/usr/bin/python3 v2/server.py                                       # http://localhost:8000
/usr/bin/python3 v2/predict.py --queue 30 --wait 60 --opp 8
```
Seeds: scenario generators 1001/2002/3003; TRAIN sim seeds (7,17,27); VALIDATION (101,102,103); TEST 3 fresh seeds per scenario from generator 3003; optimizers seeds 1,2,3; bootstrap seed 12345 (10 000 resamples); stress generator 4004; v1 legacy seed 99.
