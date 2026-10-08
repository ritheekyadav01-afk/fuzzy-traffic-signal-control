import json
import numpy as np
from simulate import run_simulation, fixed_timer_controller
from fuzzy_core import green_duration, DEFAULT_THETA
from ga_tune import run_ga, TRAIN_SCENARIOS

# full evaluation set: the 3 training scenarios PLUS 2 the GA never saw,
# to check the tuned controller generalizes rather than overfits
EVAL_SCENARIOS = {
    'light':      (0.10, 0.10),   # seen during GA training
    'moderate':   (0.20, 0.20),   # seen during GA training
    'uneven':     (0.35, 0.10),   # seen during GA training
    'rush_hour':  (0.26, 0.19),   # HELD OUT — not seen during training
    'heavy':      (0.30, 0.30),   # HELD OUT — stress test, near/at capacity
}
EVAL_DURATION = 3600
EVAL_SEED = 99   # different seed from GA training, for an honest out-of-sample test


def make_fuzzy_controller(theta):
    def controller(q, w):
        return green_duration(q, w, theta)
    return controller


def main():
    print("=" * 70)
    print("STEP 1 — Running GA (pop=24, generations=30) to tune the controller")
    print("=" * 70)
    best_theta, ga_history = run_ga(pop_size=24, generations=30, seed=1, verbose=False)
    print(f"GA finished. Best theta: {np.round(best_theta, 3)}")
    print(f"GA convergence: gen 1 = {ga_history[0]:.2f}s -> gen {len(ga_history)} = {ga_history[-1]:.2f}s\n")

    fixed_ctrl = fixed_timer_controller
    fuzzy_ctrl = make_fuzzy_controller(DEFAULT_THETA)
    ga_ctrl = make_fuzzy_controller(best_theta)

    print("=" * 70)
    print("STEP 2 — Three-way comparison across traffic scenarios")
    print("=" * 70)
    header = f"{'Scenario':<12}{'Fixed':>10}{'Fuzzy':>10}{'Fuzzy+GA':>10}{'vs Fixed':>12}{'vs Fuzzy':>12}"
    print(header)
    print("-" * len(header))

    results = {}
    for name, (r_ns, r_ew) in EVAL_SCENARIOS.items():
        fixed = run_simulation(fixed_ctrl, r_ns, r_ew, duration_seconds=EVAL_DURATION, seed=EVAL_SEED)
        fuzzy = run_simulation(fuzzy_ctrl, r_ns, r_ew, duration_seconds=EVAL_DURATION, seed=EVAL_SEED)
        ga = run_simulation(ga_ctrl, r_ns, r_ew, duration_seconds=EVAL_DURATION, seed=EVAL_SEED)

        d_fixed, d_fuzzy, d_ga = fixed['avg_delay_sec'], fuzzy['avg_delay_sec'], ga['avg_delay_sec']
        vs_fixed = (d_fixed - d_ga) / d_fixed * 100
        vs_fuzzy = (d_fuzzy - d_ga) / d_fuzzy * 100

        tag = " (held out)" if name in ('rush_hour', 'heavy') else ""
        print(f"{name+tag:<12}{d_fixed:>9.1f}s{d_fuzzy:>9.1f}s{d_ga:>9.1f}s{vs_fixed:>+11.1f}%{vs_fuzzy:>+11.1f}%")

        results[name] = {
            'fixed': d_fixed, 'fuzzy': d_fuzzy, 'fuzzy_ga': d_ga,
            'improvement_vs_fixed_pct': vs_fixed,
            'improvement_vs_fuzzy_pct': vs_fuzzy,
            'held_out': name in ('rush_hour', 'heavy'),
        }

    # headline number: average improvement vs fixed-timer across ALL scenarios
    avg_improvement = np.mean([r['improvement_vs_fixed_pct'] for r in results.values()])
    print(f"\nHEADLINE: Fuzzy+GA reduces average wait time by {avg_improvement:.1f}% "
          f"vs. fixed-timer, averaged across all 5 scenarios.")

    output = {
        'best_theta': list(np.round(best_theta, 3)),
        'default_theta': list(DEFAULT_THETA),
        'ga_history': [round(float(h), 3) for h in ga_history],
        'results': results,
        'headline_improvement_pct': round(float(avg_improvement), 1),
    }
    with open('/home/claude/traffic_project/results.json', 'w') as f:
        json.dump(output, f, indent=2)
    print("\nSaved full results to results.json")


if __name__ == "__main__":
    main()
