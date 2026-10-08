# DECK_NUMBERS - exact figures for slides (generated from results_v2.json; the existing decks/replays were NOT edited)

## 0. Read this first: which number comes from which test set

| label | set | n | what it is |
|---|---|---|---|
| **LEGACY-5** | the 5 named v1 scenarios (light, moderate, uneven, rush_hour, heavy), constant demand, seed 99, 3600 s | 5 | the numbers in the Review 3 deck (26.8 / 37.9 / 57.0). Single seed, no CI. 3 of these were GA training scenarios in v1. |
| **TEST-60** | 60 generated scenarios (6 demand profiles incl. time-varying), 3 fresh seeds each, never used for training or model selection | 60 | the honest out-of-sample evaluation of v2. Evaluated exactly once. |

## 1. Numbers already in the Review 3 deck - reproduced, and what they mean

| deck number | reproduced? | source |
|---|---|---|
| 26.8% (headline) | YES, 26.8% | v1 fuzzy+GA, mean of the 5 LEGACY scenarios vs fixed-30, seed 99 |
| 37.9% (held-out) | YES, 37.9% | mean of rush_hour and heavy (n=2!) |
| 57.0% (uneven) | YES, 57.0% | one scenario, one seed: 506.3 s -> 217.7 s |

**Numbers that DIFFER from the deck and must not be mixed with it:**

- v1 fuzzy+GA on TEST-60: **+34.9% (95% CI +29.6 to +40.3)** vs fixed-30 (not 26.8%): different, larger and harder set, includes time-varying demand.
- 'Held-out' 37.9% is the mean of only 2 scenarios; it is not a statistically meaningful held-out result. TEST-60 is the proper replacement.
- Two older figures floating around (27.8%, 32.5%) are not reproducible from this folder: 27.8% = LEGACY-5 mean with the earlier single-seed theta; 32.5% came from an earlier 9-scenario draft. Do not use them.

## 2. Headline v2 numbers (TEST-60, all paired, 95% bootstrap CI over scenarios)

Official v2 controller = `fuzzy2_bp_PSO` (fuzzy-v2, 12 breakpoint genes, PSO seed 2, chosen on VALIDATION).

| controller | mean delay (s) | reduction vs fixed-30 | reduction vs v1 fuzzy+GA | reduction vs actuated rule | W/L/T vs v1+GA | W/L/T vs actuated |
|---|---|---|---|---|---|---|
| fixed_30s | 173.5 | +0.0% (95% CI +0.0 to +0.0) | -76.8% (95% CI -97.3 to -58.4) | -313.8% (95% CI -413.0 to -226.4) | 0/60/0 | 0/60/0 |
| best_fixed_56s | 160.4 | -6.9% (95% CI -13.9 to -0.6) | -77.9% (95% CI -92.2 to -64.8) | -300.8% (95% CI -382.4 to -228.0) | 0/55/5 | 0/60/0 |
| actuated | 74.6 | +57.8% (95% CI +51.3 to +64.2) | +40.7% (95% CI +34.9 to +46.5) | +0.0% (95% CI +0.0 to +0.0) | 59/0/1 | 0/0/60 |
| fuzzy_v1_default | 121.8 | +29.4% (95% CI +24.8 to +34.3) | -11.2% (95% CI -15.4 to -7.2) | -135.6% (95% CI -175.3 to -100.8) | 12/44/4 | 0/60/0 |
| fuzzy_v1_GA_official | 105.9 | +34.9% (95% CI +29.6 to +40.3) | +0.0% (95% CI +0.0 to +0.0) | -106.2% (95% CI -134.6 to -80.3) | 0/0/60 | 0/59/1 |
| fuzzy_v2_default | 85.4 | +47.8% (95% CI +41.4 to +54.1) | +23.3% (95% CI +18.3 to +28.1) | -41.2% (95% CI -51.2 to -32.2) | 49/4/7 | 2/57/1 |
| fuzzy2_bp_PSO | 71.9 | +58.5% (95% CI +51.7 to +65.1) | +42.4% (95% CI +36.2 to +48.5) | +4.3% (95% CI +2.4 to +6.5) | 59/0/1 | 31/14/15 |

**Decision rule:** v2 vs v1+GA: mean paired reduction +42.4% (CI +36.2 to +48.5) -> promote v2 = **True**.
**Honest caveat to put on a slide:** a one-line actuated rule (green = 3 s x own queue) reaches +57.8% (95% CI +51.3 to +64.2) vs fixed-30; fuzzy-v2 beats it by only +4.3% (CI +2.4 to +6.5). v1's fuzzy+GA is far BELOW that rule.

## 3. Where it is stronger / weaker (TEST-60, % delay reduction vs fixed-30 by demand profile)

| controller | balanced_then_skewed | constant | lull | one_sided_surge | rush_ramp | surge |
|---|---|---|---|---|---|---|
| best_fixed_56s | +4.8% | +6.2% | -56.9% | +1.7% | +2.1% | -15.9% |
| actuated | +83.0% | +57.9% | +42.5% | +74.0% | +49.7% | +42.6% |
| fuzzy_v1_GA_official | +44.8% | +42.3% | +11.3% | +47.6% | +33.7% | +22.2% |
| fuzzy_v2_default | +70.2% | +50.8% | +35.4% | +62.7% | +37.3% | +30.5% |
| fuzzy2_bp_PSO | +84.8% | +59.5% | +41.6% | +75.3% | +49.7% | +42.0% |

(best_fixed_56s is the fixed timer that minimises raw mean delay on TRAIN; it LOSES badly on lull/surge, which is why its mean is negative.)

## 4. Other metrics on TEST-60 (means over scenarios)

| controller | p95 queue (veh) | max queue (veh) | worst-direction avg delay (s) | served / arrived |
|---|---|---|---|---|
| fixed_30s | 168.8 | 183.0 | 223.5 | 0.910 |
| actuated | 82.9 | 92.0 | 88.0 | 0.969 |
| fuzzy_v1_GA_official | 108.8 | 119.7 | 126.9 | 0.953 |
| fuzzy2_bp_PSO | 80.3 | 89.4 | 82.8 | 0.971 |

## 5. The 5 LEGACY scenarios with v2 (seed 99, same as the deck; single seed, no CI)

| controller | light | moderate | uneven | rush_hour | heavy | mean of 5 | held-out mean (rush_hour, heavy) |
|---|---|---|---|---|---|---|---|
| fixed_30s | 13.3s (+0.0%) | 24.4s (+0.0%) | 506.3s (+0.0%) | 191.5s (+0.0%) | 465.4s (+0.0%) | +0.0% | +0.0% |
| actuated | 8.0s (+39.9%) | 20.8s (+14.5%) | 49.2s (+90.3%) | 43.5s (+77.3%) | 396.4s (+14.8%) | +47.3% | +46.0% |
| fuzzy_v1_GA_official | 13.3s (+0.1%) | 24.1s (+1.3%) | 217.7s (+57.0%) | 70.0s (+63.5%) | 407.9s (+12.3%) | +26.8% | +37.9% |
| fuzzy2_bp_PSO | 8.2s (+38.5%) | 20.8s (+14.5%) | 39.0s (+92.3%) | 40.1s (+79.0%) | 398.7s (+14.3%) | +47.7% | +46.7% |

Note: in `heavy` (0.30+0.30 veh/s = 0.60 > capacity) the system is over-saturated; no controller can do much (all within 396-466 s).

## 6. Robustness beyond the training range (stress set, NOT used for any decision)

24 constant-demand scenarios with rates U(0.03,0.55) per direction (generators stop at 0.40), fresh seeds. Mean % vs fixed-30:

| controller | mean delay (s) | reduction vs fixed-30 | worst scenario |
|---|---|---|---|
| fixed_30s | 552.8 | +0.0% (CI +0.0 to +0.0) | +0.0% |
| best_fixed_56s | 524.3 | -2.5% (CI -12.3 to +5.8) | -59.2% |
| actuated | 411.4 | +32.0% (CI +22.0 to +43.1) | +3.2% |
| fuzzy_v1_GA_official | 453.4 | +20.5% (CI +14.0 to +28.1) | +3.0% |
| fuzzy_v2_default | 419.1 | +27.4% (CI +18.2 to +37.7) | +3.0% |
| fuzzy2_bp_PSO | 404.1 | +33.1% (CI +22.8 to +44.6) | +3.1% |

## 7. Optimizer comparison (Week 7-9 material; same fitness, 2000 evaluations, 3 seeds each)

| structure | optimizer | train fitness (mean ± sd over 3 seeds) | best train | validation (mean) | best validation | evals to reach 95% of final improvement | wall s/run |
|---|---|---|---|---|---|---|---|
| fuzzy1_new | GA | 0.6391 ± 0.0001 | 0.6390 | 0.7135 | 0.7124 | 383 | 1891 |
| fuzzy1_new | PSO | 0.6392 ± 0.0008 | 0.6381 | 0.7048 | 0.6979 | 367 | 1657 |
| fuzzy1_new | SA | 0.6395 ± 0.0002 | 0.6393 | 0.7141 | 0.7130 | 713 | 1605 |
| fuzzy2_bp | GA | 0.4143 ± 0.0019 | 0.4126 | 0.5103 | 0.5090 | 637 | 2348 |
| fuzzy2_bp | PSO | 0.4186 ± 0.0047 | 0.4119 | 0.5156 | 0.5079 | 590 | 2367 |
| fuzzy2_bp | SA | 0.4189 ± 0.0017 | 0.4165 | 0.5151 | 0.5132 | 723 | 2383 |
| fuzzy2_bpw | GA | 0.4157 ± 0.0014 | 0.4143 | 0.5162 | 0.5131 | 940 | 2426 |
| fuzzy2_bpw | PSO | 0.4139 ± 0.0010 | 0.4126 | 0.5122 | 0.5102 | 790 | 2472 |
| fuzzy2_bpw | SA | 0.4183 ± 0.0050 | 0.4131 | 0.5210 | 0.5133 | 1183 | 2523 |


Take-aways that are actually supported: (a) all three optimizers converge to nearly the same quality (differences <= 0.005 in fitness ~ the seed-to-seed spread); (b) the gain comes from the controller STRUCTURE: re-training v1's 3-centre controller on the new data gives 0.639 TRAIN fitness vs 0.414 for fuzzy-v2; (c) adding 27 rule weights (39 genes) did not help.

## 8. Facts for the 'what is v2' slide

- fuzzy-v2: 3 inputs (own queue, waiting time, **opposing queue**), 27 rules, output universe 0-80 s clamped to 10-60 s; 12 tunable breakpoints (ordered-partition repair keeps every candidate valid).
- Data: 40 TRAIN / 20 VALIDATION / 60 TEST generated scenarios, fixed seeds; fitness = mean delay relative to the best fixed timer so light traffic is not drowned out.
- Simulator v2 reproduces v1 bit-for-bit on constant demand (max relative difference 0.0).
- 23 unit tests pass.

