# Intelligent Traffic Signal Control — Fuzzy Logic + Genetic Algorithm

## Files
- `fuzzy_core.py`   — Mamdani fuzzy controller, GA-tunable (3 membership centers)
- `simulate.py`     — 2-phase intersection simulator (Poisson arrivals, queueing, delay tracking)
- `ga_tune.py`      — Genetic algorithm that tunes the fuzzy controller's membership centers
- `final_comparison.py` — Runs everything: GA tuning + 3-way comparison (fixed-timer vs fuzzy vs fuzzy+GA)
- `results.json`    — Output of the last run (GA convergence history + full comparison results)

## How to run
```
pip install numpy
python3 final_comparison.py
```
Takes under a minute. Prints the full comparison table and saves results.json.

## Headline result
Fuzzy+GA reduces average vehicle wait time by 27.8% vs. a fixed-timer baseline,
averaged across 5 traffic scenarios — including 2 the GA never trained on
(rush_hour, heavy), confirming the tuned controller generalizes.

## What's next (Review 3 scope)
- Animated visual intersection (cars + live signal) for the demo
- Extend to a small multi-intersection network
- Compare GA against PSO and Simulated Annealing (both taught in Weeks 7-9)
