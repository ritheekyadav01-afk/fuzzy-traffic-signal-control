from simulate import run_simulation, fixed_timer_controller
from fuzzy_core import green_duration, DEFAULT_THETA

SCENARIOS = {
    'light':    (0.10, 0.10),
    'moderate': (0.20, 0.20),
    'heavy':    (0.30, 0.30),
    'uneven':   (0.35, 0.10),   # NS much busier than EW
}

def fuzzy_controller(queue, waiting_time):
    return green_duration(queue, waiting_time, DEFAULT_THETA)

print(f"{'Scenario':<10} {'Fixed-timer':>14} {'Fuzzy-only':>14} {'Improvement':>14}")
print("-" * 56)
for name, (r_ns, r_ew) in SCENARIOS.items():
    fixed = run_simulation(fixed_timer_controller, r_ns, r_ew, duration_seconds=3600, seed=42)
    fuzzy = run_simulation(fuzzy_controller, r_ns, r_ew, duration_seconds=3600, seed=42)
    improvement = (fixed['avg_delay_sec'] - fuzzy['avg_delay_sec']) / fixed['avg_delay_sec'] * 100
    print(f"{name:<10} {fixed['avg_delay_sec']:>12.2f}s {fuzzy['avg_delay_sec']:>12.2f}s {improvement:>+13.1f}%")
