# RESULTS (VALIDATION DRY RUN - not the official numbers)

Set: **validation**, 20 scenarios x 3 traffic seeds (seeds are averaged inside a scenario; the scenario is the unit of analysis). All controllers see identical pre-drawn arrivals (paired). CIs = 95% bootstrap (10000 resamples over scenarios) of the mean per-scenario % delay reduction. Win/loss/tie = scenarios where delay is lower / higher / within 1% of the reference.

Official fuzzy-v2 candidate (chosen by VALIDATION score only): `fuzzy2_bp_PSO`

## Table A - all controllers

| controller | mean delay (s) | vs fixed-30 | vs best-fixed-29 | vs v1 fuzzy+GA | vs actuated | W/L/T vs fixed-30 | W/L/T vs v1+GA | worst case vs fixed-30 | mean p95 queue | worst-dir delay (s) | served/arrived |
|---|---|---|---|---|---|---|---|---|---|---|---|
| fixed_30s | 207.1 | +0.0% [+0.0, +0.0] | -0.2% [-1.6, +1.1] | -54.7% [-82.9, -32.9] | -193.8% [-343.5, -93.1] | 0/0/20 | 0/20/0 | +0.0% (validation_00_constant) | 223.5 | 271.7 | 0.907 |
| best_fixed_29s | 208.4 | +0.1% [-1.2, +1.4] | +0.0% [+0.0, +0.0] | -54.7% [-83.1, -32.6] | -194.0% [-345.4, -92.2] | 6/7/7 | 0/20/0 | -4.6% (validation_02_rush_ramp) | 225.3 | 273.3 | 0.907 |
| best_fixed_56s | 191.7 | -5.8% [-18.1, +5.0] | -6.4% [-19.7, +5.3] | -57.3% [-80.2, -38.7] | -192.3% [-321.1, -104.2] | 14/6/0 | 1/17/2 | -57.0% (validation_19_lull) | 205.9 | 249.5 | 0.915 |
| actuated | 128.8 | +48.5% [+38.2, +59.5] | +48.4% [+38.3, +59.4] | +31.2% [+21.8, +41.2] | +0.0% [+0.0, +0.0] | 20/0/0 | 20/0/0 | +7.4% (validation_00_constant) | 153.4 | 155.8 | 0.946 |
| pressure_split | 145.8 | +19.6% [-0.1, +38.8] | +19.0% [-1.5, +38.6] | -5.2% [-22.8, +12.1] | -58.2% [-83.5, -34.9] | 15/5/0 | 8/12/0 | -54.8% (validation_19_lull) | 165.8 | 149.6 | 0.942 |
| longest_queue_first | 143.3 | +16.2% [-6.1, +36.9] | +15.5% [-7.7, +36.8] | -9.5% [-30.0, +9.7] | -67.0% [-97.6, -38.3] | 15/5/0 | 7/12/1 | -67.4% (validation_19_lull) | 161.3 | 154.2 | 0.943 |
| fuzzy_v1_default | 166.1 | +23.6% [+17.6, +30.5] | +23.4% [+17.3, +30.5] | -10.3% [-15.9, -5.0] | -88.3% [-137.7, -49.0] | 20/0/0 | 4/15/1 | +3.8% (validation_00_constant) | 188.7 | 207.2 | 0.928 |
| fuzzy_v1_GA_official | 151.5 | +28.9% [+21.0, +37.5] | +28.7% [+20.6, +37.4] | +0.0% [+0.0, +0.0] | -67.3% [-104.0, -37.6] | 20/0/0 | 0/0/20 | +6.0% (validation_00_constant) | 173.6 | 177.9 | 0.936 |
| fuzzy_v2_default | 139.9 | +39.8% [+30.1, +50.4] | +39.8% [+30.3, +50.3] | +17.7% [+9.7, +26.0] | -26.4% [-39.5, -15.5] | 20/0/0 | 13/3/4 | +6.4% (validation_00_constant) | 161.2 | 158.8 | 0.944 |
| fuzzy2_bp_GA | 127.3 | +49.2% [+38.5, +60.5] | +49.1% [+38.7, +60.4] | +32.5% [+22.5, +43.1] | +3.0% [+0.4, +6.2] | 20/0/0 | 20/0/0 | +7.2% (validation_00_constant) | 152.2 | 152.1 | 0.947 |
| fuzzy2_bp_PSO **(official v2 candidate)** | 126.9 | +49.3% [+38.7, +60.7] | +49.3% [+38.8, +60.6] | +32.7% [+22.7, +43.4] | +3.5% [+0.5, +7.0] | 20/0/0 | 20/0/0 | +7.1% (validation_00_constant) | 152.0 | 150.5 | 0.948 |
| fuzzy2_bp_SA | 127.9 | +48.7% [+38.5, +59.7] | +48.7% [+38.6, +59.6] | +31.6% [+22.4, +41.5] | +0.6% [-0.4, +1.6] | 20/0/0 | 20/0/0 | +7.3% (validation_00_constant) | 152.8 | 153.2 | 0.947 |
| fuzzy2_bpw_GA | 128.8 | +48.7% [+38.0, +60.3] | +48.7% [+38.1, +60.2] | +31.9% [+21.6, +42.9] | +2.6% [-0.6, +6.2] | 20/0/0 | 18/0/2 | +6.6% (validation_00_constant) | 153.8 | 154.2 | 0.947 |
| oracle_fixed_UNREALISABLE | 186.5 | +15.7% [+10.5, +21.8] | +15.7% [+10.8, +21.4] | -32.1% [-58.3, -9.8] | -153.2% [-285.2, -60.9] | 20/0/0 | 5/13/2 | +3.8% (validation_02_rush_ramp) | nan | nan | nan |

`oracle_fixed_UNREALISABLE` picks the best fixed duration with hindsight on each run: a headroom reference, not a deployable controller.

Also vs the best fixed timer chosen by raw mean delay (56 s):

| controller | vs best-fixed-56 | W/L/T |
|---|---|---|
| fixed_30s | +0.3% [-8.8, +9.8] | 6/14/0 |
| best_fixed_29s | +0.1% [-9.6, +10.1] | 6/14/0 |
| best_fixed_56s | +0.0% [+0.0, +0.0] | 0/0/20 |
| actuated | +49.3% [+37.7, +61.2] | 20/0/0 |
| pressure_split | +26.7% [+14.1, +40.8] | 16/3/1 |
| longest_queue_first | +24.8% [+12.1, +38.8] | 13/4/3 |
| fuzzy_v1_default | +24.7% [+16.0, +33.4] | 16/3/1 |
| fuzzy_v1_GA_official | +31.1% [+22.6, +39.5] | 17/1/2 |
| fuzzy_v2_default | +40.4% [+28.2, +52.5] | 18/1/1 |
| fuzzy2_bp_GA | +50.0% [+37.9, +62.2] | 20/0/0 |
| fuzzy2_bp_PSO | +50.2% [+38.0, +62.3] | 20/0/0 |
| fuzzy2_bp_SA | +49.7% [+38.0, +61.4] | 20/0/0 |
| fuzzy2_bpw_GA | +49.4% [+36.8, +62.0] | 20/0/0 |
| oracle_fixed_UNREALISABLE | +15.0% [+6.2, +25.6] | 14/0/6 |

## Decision rule

- Rule: promote v2 only if mean paired reduction vs v1+GA > 0 and the 95% bootstrap CI excludes zero.
- fuzzy-v2 candidate `fuzzy2_bp_PSO` vs v1 fuzzy+GA: mean paired reduction **+32.7%**, 95% CI [+22.7, +43.4] -> **promote v2: True**.
- Same candidate vs the simple actuated rule: mean paired reduction +3.5%, 95% CI [+0.5, +7.0] (positive = fuzzy-v2 better).

## Table B - by demand profile (mean % delay reduction vs fixed-30)

| controller | balanced_then_skewed | constant | lull | one_sided_surge | rush_ramp | surge |
|---|---|---|---|---|---|---|
| best_fixed_56s | +5.6% | +11.9% | -53.0% | +4.1% | -7.0% | -10.6% |
| actuated | +77.9% | +38.1% | +42.1% | +73.3% | +35.5% | +44.0% |
| fuzzy_v1_GA_official | +42.6% | +28.7% | +11.7% | +47.6% | +22.2% | +25.7% |
| fuzzy_v2_default | +68.5% | +30.3% | +36.9% | +64.7% | +23.6% | +34.0% |
| fuzzy2_bp_PSO | +82.8% | +38.3% | +41.9% | +75.0% | +35.6% | +44.4% |

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
| fuzzy_v2_default | 9.2s (+30.5%) | 26.6s (-9.1%) | 73.8s (+85.4%) | 62.9s (+67.2%) | 406.1s (+12.7%) | +37.4% | +40.0% |
| fuzzy2_bp_GA | 8.2s (+38.2%) | 20.9s (+14.1%) | 43.4s (+91.4%) | 41.0s (+78.6%) | 398.9s (+14.3%) | +47.3% | +46.4% |
| fuzzy2_bp_PSO | 8.2s (+38.5%) | 20.8s (+14.5%) | 39.0s (+92.3%) | 40.1s (+79.0%) | 398.7s (+14.3%) | +47.7% | +46.7% |
| fuzzy2_bp_SA | 8.8s (+33.3%) | 20.8s (+14.5%) | 52.3s (+89.7%) | 42.2s (+78.0%) | 397.1s (+14.7%) | +46.0% | +46.3% |
| fuzzy2_bpw_GA | 7.9s (+40.6%) | 21.0s (+14.0%) | 45.5s (+91.0%) | 42.8s (+77.7%) | 403.7s (+13.3%) | +47.3% | +45.5% |

v1 reference (baseline_v1.json): v1 fuzzy+GA = light 13.3s, moderate 24.1s, uneven 217.7s, rush_hour 70.0s, heavy 407.9s; mean of 5 = 26.8%, held-out mean = 37.9%.
