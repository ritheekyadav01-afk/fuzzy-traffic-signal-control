# RESULTS (official: TEST set, evaluated once)

Set: **test**, 60 scenarios x 3 traffic seeds (seeds are averaged inside a scenario; the scenario is the unit of analysis). All controllers see identical pre-drawn arrivals (paired). CIs = 95% bootstrap (10000 resamples over scenarios) of the mean per-scenario % delay reduction. Win/loss/tie = scenarios where delay is lower / higher / within 1% of the reference.

Official fuzzy-v2 candidate (chosen by VALIDATION score only): `fuzzy2_bp_PSO`

## Table A - all controllers

| controller | mean delay (s) | vs fixed-30 | vs best-fixed-29 | vs v1 fuzzy+GA | vs actuated | W/L/T vs fixed-30 | W/L/T vs v1+GA | worst case vs fixed-30 | mean p95 queue | worst-dir delay (s) | served/arrived |
|---|---|---|---|---|---|---|---|---|---|---|---|
| fixed_30s | 173.5 | +0.0% [+0.0, +0.0] | +0.1% [-0.7, +0.9] | -76.8% [-97.3, -58.4] | -313.8% [-413.0, -226.4] | 0/0/60 | 0/60/0 | +0.0% (test_00_constant) | 168.8 | 223.5 | 0.910 |
| best_fixed_29s | 174.6 | -0.2% [-1.0, +0.6] | +0.0% [+0.0, +0.0] | -77.4% [-98.4, -58.6] | -315.5% [-415.6, -227.0] | 13/25/22 | 0/60/0 | -7.0% (test_54_lull) | 170.0 | 224.9 | 0.910 |
| best_fixed_56s | 160.4 | -6.9% [-13.9, -0.6] | -6.9% [-14.0, -0.4] | -77.9% [-92.2, -64.8] | -300.8% [-382.4, -228.0] | 38/21/1 | 0/55/5 | -65.5% (test_40_lull) | 154.3 | 204.0 | 0.918 |
| actuated | 74.6 | +57.8% [+51.3, +64.2] | +57.9% [+51.5, +64.2] | +40.7% [+34.9, +46.5] | +0.0% [+0.0, +0.0] | 60/0/0 | 59/0/1 | +6.5% (test_43_constant) | 82.9 | 88.0 | 0.969 |
| pressure_split | 88.4 | +24.9% [+11.3, +37.7] | +24.8% [+11.2, +37.7] | -2.7% [-15.5, +9.7] | -74.4% [-90.2, -59.1] | 45/15/0 | 25/35/0 | -74.4% (test_40_lull) | 90.4 | 91.6 | 0.966 |
| longest_queue_first | 87.8 | +23.1% [+9.5, +36.3] | +23.0% [+9.2, +36.2] | -6.0% [-19.1, +6.6] | -82.1% [-98.6, -65.8] | 45/15/0 | 24/32/4 | -77.1% (test_40_lull) | 88.7 | 95.0 | 0.967 |
| fuzzy_v1_default | 121.8 | +29.4% [+24.8, +34.3] | +29.6% [+24.9, +34.4] | -11.2% [-15.4, -7.2] | -135.6% [-175.3, -100.8] | 60/0/0 | 12/44/4 | +3.6% (test_43_constant) | 125.3 | 151.3 | 0.942 |
| fuzzy_v1_GA_official | 105.9 | +34.9% [+29.6, +40.3] | +35.0% [+29.6, +40.4] | +0.0% [+0.0, +0.0] | -106.2% [-134.6, -80.3] | 60/0/0 | 0/0/60 | +5.0% (test_40_lull) | 108.8 | 126.9 | 0.953 |
| fuzzy1_new_GA | 111.1 | +36.1% [+31.4, +40.9] | +36.2% [+31.6, +40.9] | +0.2% [-2.4, +2.8] | -109.6% [-142.9, -80.2] | 60/0/0 | 23/34/3 | +4.3% (test_43_constant) | 114.6 | 134.3 | 0.950 |
| fuzzy1_new_PSO | 108.6 | +36.2% [+31.2, +41.2] | +36.3% [+31.4, +41.3] | +1.3% [-0.6, +3.2] | -104.9% [-135.3, -77.7] | 60/0/0 | 24/33/3 | +4.7% (test_43_constant) | 112.2 | 131.1 | 0.951 |
| fuzzy1_new_SA | 111.5 | +35.7% [+30.9, +40.6] | +35.8% [+31.0, +40.6] | -0.1% [-2.9, +2.7] | -109.6% [-142.8, -80.4] | 60/0/0 | 22/35/3 | +4.3% (test_43_constant) | 115.2 | 134.9 | 0.949 |
| fuzzy_v2_default | 85.4 | +47.8% [+41.4, +54.1] | +47.9% [+41.5, +54.2] | +23.3% [+18.3, +28.1] | -41.2% [-51.2, -32.2] | 60/0/0 | 49/4/7 | +4.8% (test_58_rush_ramp) | 89.9 | 97.4 | 0.966 |
| fuzzy2_bp_GA | 72.6 | +58.3% [+51.6, +64.9] | +58.4% [+51.7, +64.9] | +41.9% [+35.8, +48.1] | +3.2% [+1.7, +5.1] | 60/0/0 | 59/0/1 | +6.3% (test_43_constant) | 81.0 | 84.4 | 0.970 |
| fuzzy2_bp_PSO **(official v2 candidate)** | 71.9 | +58.5% [+51.7, +65.1] | +58.6% [+51.8, +65.1] | +42.4% [+36.2, +48.5] | +4.3% [+2.4, +6.5] | 60/0/0 | 59/0/1 | +6.3% (test_43_constant) | 80.3 | 82.8 | 0.971 |
| fuzzy2_bp_SA | 73.8 | +57.9% [+51.4, +64.2] | +58.0% [+51.5, +64.3] | +40.9% [+35.1, +46.6] | -0.0% [-0.9, +0.9] | 60/0/0 | 59/0/1 | +6.5% (test_43_constant) | 81.9 | 86.5 | 0.970 |
| fuzzy2_bpw_GA | 73.3 | +58.0% [+51.2, +64.7] | +58.1% [+51.3, +64.7] | +41.7% [+35.4, +48.0] | +3.5% [+1.8, +5.4] | 60/0/0 | 56/0/4 | +5.7% (test_43_constant) | 81.8 | 85.0 | 0.970 |
| fuzzy2_bpw_PSO | 72.1 | +58.4% [+51.6, +65.1] | +58.5% [+51.8, +65.1] | +42.3% [+36.0, +48.5] | +4.4% [+2.4, +6.7] | 60/0/0 | 56/0/4 | +5.8% (test_43_constant) | 80.7 | 82.8 | 0.971 |
| fuzzy2_bpw_SA | 72.7 | +58.1% [+51.3, +64.8] | +58.2% [+51.5, +64.9] | +41.9% [+35.6, +48.1] | +3.6% [+1.8, +5.6] | 60/0/0 | 56/0/4 | +5.9% (test_43_constant) | 81.2 | 83.9 | 0.970 |
| oracle_fixed_UNREALISABLE | 154.6 | +16.3% [+13.4, +19.3] | +16.5% [+13.7, +19.6] | -49.5% [-67.0, -33.1] | -254.7% [-340.4, -178.2] | 60/0/0 | 12/43/5 | +4.0% (test_55_balanced_then_skewed) | nan | nan | nan |

`oracle_fixed_UNREALISABLE` picks the best fixed duration with hindsight on each run: a headroom reference, not a deployable controller.

Also vs the best fixed timer chosen by raw mean delay (56 s):

| controller | vs best-fixed-56 | W/L/T |
|---|---|---|
| fixed_30s | +1.8% [-3.0, +6.8] | 21/38/1 |
| best_fixed_29s | +1.4% [-3.5, +6.7] | 20/40/0 |
| best_fixed_56s | +0.0% [+0.0, +0.0] | 0/0/60 |
| actuated | +60.4% [+53.5, +66.8] | 60/0/0 |
| pressure_split | +35.0% [+26.0, +43.9] | 40/19/1 |
| longest_queue_first | +33.6% [+24.8, +42.4] | 41/13/6 |
| fuzzy_v1_default | +32.8% [+28.0, +37.4] | 53/6/1 |
| fuzzy_v1_GA_official | +38.8% [+34.1, +43.3] | 55/0/5 |
| fuzzy1_new_GA | +38.9% [+33.8, +43.7] | 53/5/2 |
| fuzzy1_new_PSO | +39.4% [+34.3, +44.1] | 55/2/3 |
| fuzzy1_new_SA | +38.5% [+33.3, +43.4] | 51/5/4 |
| fuzzy_v2_default | +50.7% [+44.0, +57.0] | 54/2/4 |
| fuzzy2_bp_GA | +61.0% [+54.0, +67.5] | 59/0/1 |
| fuzzy2_bp_PSO | +61.3% [+54.2, +67.8] | 59/0/1 |
| fuzzy2_bp_SA | +60.6% [+53.7, +66.9] | 60/0/0 |
| fuzzy2_bpw_GA | +60.7% [+53.5, +67.4] | 57/0/3 |
| fuzzy2_bpw_PSO | +61.1% [+54.0, +67.7] | 58/0/2 |
| fuzzy2_bpw_SA | +60.9% [+53.7, +67.5] | 58/0/2 |
| oracle_fixed_UNREALISABLE | +16.3% [+10.9, +22.3] | 48/0/12 |

## Decision rule

- Rule: promote v2 only if mean paired reduction vs v1+GA > 0 and the 95% bootstrap CI excludes zero.
- fuzzy-v2 candidate `fuzzy2_bp_PSO` vs v1 fuzzy+GA: mean paired reduction **+42.4%**, 95% CI [+36.2, +48.5] -> **promote v2: True**.
- Same candidate vs the simple actuated rule: mean paired reduction +4.3%, 95% CI [+2.4, +6.5] (positive = fuzzy-v2 better).

## Table B - by demand profile (mean % delay reduction vs fixed-30)

| controller | balanced_then_skewed | constant | lull | one_sided_surge | rush_ramp | surge |
|---|---|---|---|---|---|---|
| best_fixed_56s | +4.8% | +6.2% | -56.9% | +1.7% | +2.1% | -15.9% |
| actuated | +83.0% | +57.9% | +42.5% | +74.0% | +49.7% | +42.6% |
| fuzzy_v1_GA_official | +44.8% | +42.3% | +11.3% | +47.6% | +33.7% | +22.2% |
| fuzzy_v2_default | +70.2% | +50.8% | +35.4% | +62.7% | +37.3% | +30.5% |
| fuzzy2_bp_PSO | +84.8% | +59.5% | +41.6% | +75.3% | +49.7% | +42.0% |

## Table C - the 5 legacy (v1/deck) scenarios, seed 99 (single seed, no CI)

| controller | light | moderate | uneven | rush_hour | heavy | mean of 5 | mean of held-out (rush_hour, heavy) |
|---|---|---|---|---|---|---|---|
| fixed_30s | 13.3s (+0.0%) | 24.4s (+0.0%) | 506.3s (+0.0%) | 191.5s (+0.0%) | 465.4s (+0.0%) | +0.0% | +0.0% |
| best_fixed_29s | 13.5s (-1.6%) | 24.9s (-2.1%) | 508.2s (-0.4%) | 193.6s (-1.1%) | 468.9s (-0.7%) | -1.2% | -0.9% |
| best_fixed_56s | 22.0s (-65.5%) | 31.9s (-30.9%) | 469.5s (+7.3%) | 166.4s (+13.1%) | 409.7s (+12.0%) | -12.8% | +12.5% |
| actuated | 8.0s (+39.9%) | 20.8s (+14.5%) | 49.2s (+90.3%) | 43.5s (+77.3%) | 396.4s (+14.8%) | +47.3% | +46.0% |
| pressure_split | 22.8s (-71.6%) | 31.0s (-27.2%) | 56.6s (+88.8%) | 54.1s (+71.8%) | 438.6s (+5.8%) | +13.5% | +38.8% |
| longest_queue_first | 22.7s (-71.1%) | 34.9s (-43.3%) | 66.6s (+86.8%) | 58.3s (+69.5%) | 409.9s (+11.9%) | +10.8% | +40.7% |
| fuzzy_v1_default | 12.8s (+3.3%) | 23.9s (+1.7%) | 338.3s (+33.2%) | 86.8s (+54.7%) | 428.2s (+8.0%) | +20.2% | +31.3% |
| fuzzy_v1_GA_official | 13.3s (+0.1%) | 24.1s (+1.3%) | 217.7s (+57.0%) | 70.0s (+63.5%) | 407.9s (+12.3%) | +26.8% | +37.9% |
| fuzzy1_new_GA | 10.8s (+18.4%) | 23.6s (+3.0%) | 253.6s (+49.9%) | 93.5s (+51.2%) | 422.3s (+9.3%) | +26.3% | +30.2% |
| fuzzy1_new_PSO | 11.4s (+14.1%) | 22.4s (+8.2%) | 242.0s (+52.2%) | 80.8s (+57.8%) | 417.0s (+10.4%) | +28.5% | +34.1% |
| fuzzy1_new_SA | 11.2s (+15.9%) | 23.2s (+4.7%) | 260.1s (+48.6%) | 99.7s (+47.9%) | 421.9s (+9.4%) | +25.3% | +28.6% |
| fuzzy_v2_default | 9.2s (+30.5%) | 26.6s (-9.1%) | 73.8s (+85.4%) | 62.9s (+67.2%) | 406.1s (+12.7%) | +37.4% | +40.0% |
| fuzzy2_bp_GA | 8.2s (+38.2%) | 20.9s (+14.1%) | 43.4s (+91.4%) | 41.0s (+78.6%) | 398.9s (+14.3%) | +47.3% | +46.4% |
| fuzzy2_bp_PSO | 8.2s (+38.5%) | 20.8s (+14.5%) | 39.0s (+92.3%) | 40.1s (+79.0%) | 398.7s (+14.3%) | +47.7% | +46.7% |
| fuzzy2_bp_SA | 8.8s (+33.3%) | 20.8s (+14.5%) | 52.3s (+89.7%) | 42.2s (+78.0%) | 397.1s (+14.7%) | +46.0% | +46.3% |
| fuzzy2_bpw_GA | 7.9s (+40.6%) | 21.0s (+14.0%) | 45.5s (+91.0%) | 42.8s (+77.7%) | 403.7s (+13.3%) | +47.3% | +45.5% |
| fuzzy2_bpw_PSO | 8.3s (+37.3%) | 20.6s (+15.5%) | 40.8s (+91.9%) | 41.1s (+78.5%) | 403.1s (+13.4%) | +47.3% | +46.0% |
| fuzzy2_bpw_SA | 8.2s (+38.0%) | 21.0s (+13.6%) | 40.1s (+92.1%) | 40.8s (+78.7%) | 402.8s (+13.5%) | +47.2% | +46.1% |

v1 reference (baseline_v1.json): v1 fuzzy+GA = light 13.3s, moderate 24.1s, uneven 217.7s, rush_hour 70.0s, heavy 407.9s; mean of 5 = 26.8%, held-out mean = 37.9%.

## Table D - optimizers (same fitness, 2000 evals each, 3 seeds)

Fitness = mean over TRAIN (scenario,seed) of delay / delay(best fixed 29 s); lower is better; <1 beats best-fixed.

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

