# PROGRESS LOG (v2 autonomous build)

Conventions: all commands use `/usr/bin/python3` (3.9.6, numpy 2.0.2, **no matplotlib** -> no charts). 10 CPU cores.

## [setup] Backup + git
- Backup copy: `../traffic_project_backup_1791471006`. `git init`, committed everything, tag `v1-verified`.
- v1 files are frozen; all v2 work lives in `v2/`.
- NOTE on v1 state: `results.json` currently holds the *old* GA run (theta 26.36/28.995/49.378; uneven GA 228.9s) and
  the traces/replays were recorded from it. The *multi-seed* GA run (theta 32.784/30.785/52.154; uneven 217.7s = 57.0%) is in
  `results_multiseed.json`. The brief calls the latter "v1 official", so the baseline file records BOTH and v2 compares against the multi-seed one.
