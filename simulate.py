"""
simulate.py
-----------
A lightweight 2-phase (NS / EW) traffic intersection simulation.

Model:
- Time-stepped at 1-second resolution.
- Vehicles arrive at each approach via a Poisson process (per-second rate).
- The signal alternates NS-green / EW-green. A controller function decides
  how long each green phase lasts, given that direction's current queue
  length and its "waiting_time" (seconds since it last had green — a proxy
  for how long its longest-waiting vehicle has waited).
- During a green phase, vehicles depart at a fixed saturation flow rate.
- A small fixed clearance (amber + all-red) separates phases.

Delay is measured via the standard cumulative-count method: at every
second, the number of vehicles currently queued (in either direction)
contributes one "vehicle-second" of delay. Average delay per vehicle =
total vehicle-seconds of delay / total vehicles that arrived. This is the
same method used in the traffic-engineering literature for exactly this
kind of simplified signal-timing study (e.g. Pappis & Mamdani, 1977).

controller_fn signature: controller_fn(queue, waiting_time) -> green_seconds
(both the fixed-timer and fuzzy controllers conform to this interface.)
"""

import numpy as np

SATURATION_FLOW_PER_SEC = 0.5   # vehicles that can depart per second of green
CLEARANCE_SECONDS = 3            # amber + all-red between phases
MIN_GREEN = 10
MAX_GREEN = 60


def run_simulation(controller_fn, arrival_rate_ns, arrival_rate_ew,
                    duration_seconds=3600, seed=0, on_tick=None):
    """
    Run one simulation and return a dict of metrics.
    on_tick: optional callback(t, queue_ns, queue_ew, phase, cumulative_delay),
             called once per simulated second; phase is 'NS'|'EW'|'clearance'.
    arrival_rate_* : vehicles/second (Poisson rate) for each approach.
    """
    rng = np.random.default_rng(seed)

    queue = {'NS': 0.0, 'EW': 0.0}
    time_since_green = {'NS': 0.0, 'EW': 0.0}  # "waiting_time" proxy
    total_vehicle_seconds_delay = 0.0
    total_vehicles_arrived = 0

    t = 0
    current_phase = 'NS'

    while t < duration_seconds:
        # 1. controller decides this phase's green duration
        green = controller_fn(queue[current_phase], time_since_green[current_phase])
        green = max(MIN_GREEN, min(MAX_GREEN, green))
        other_phase = 'EW' if current_phase == 'NS' else 'NS'

        # 2. run the green phase second-by-second
        for _ in range(int(round(green))):
            if t >= duration_seconds:
                break
            arrivals_ns = rng.poisson(arrival_rate_ns)
            arrivals_ew = rng.poisson(arrival_rate_ew)
            queue['NS'] += arrivals_ns
            queue['EW'] += arrivals_ew
            total_vehicles_arrived += arrivals_ns + arrivals_ew

            served = min(queue[current_phase], SATURATION_FLOW_PER_SEC)
            queue[current_phase] -= served

            total_vehicle_seconds_delay += queue['NS'] + queue['EW']
            time_since_green[other_phase] += 1
            t += 1
            if on_tick:
                on_tick(t, queue['NS'], queue['EW'], current_phase,
                        total_vehicle_seconds_delay)

        # 3. clearance interval (no departures, arrivals still happen)
        for _ in range(CLEARANCE_SECONDS):
            if t >= duration_seconds:
                break
            arrivals_ns = rng.poisson(arrival_rate_ns)
            arrivals_ew = rng.poisson(arrival_rate_ew)
            queue['NS'] += arrivals_ns
            queue['EW'] += arrivals_ew
            total_vehicles_arrived += arrivals_ns + arrivals_ew
            total_vehicle_seconds_delay += queue['NS'] + queue['EW']
            time_since_green['NS'] += 1
            time_since_green['EW'] += 1
            t += 1
            if on_tick:
                on_tick(t, queue['NS'], queue['EW'], 'clearance',
                        total_vehicle_seconds_delay)

        # phase that just finished resets its "waiting" clock
        time_since_green[current_phase] = 0
        current_phase = other_phase

    avg_delay = (total_vehicle_seconds_delay / total_vehicles_arrived
                 if total_vehicles_arrived > 0 else 0.0)

    return {
        'avg_delay_sec': avg_delay,
        'total_vehicles': total_vehicles_arrived,
        'final_queue_ns': queue['NS'],
        'final_queue_ew': queue['EW'],
    }


def fixed_timer_controller(queue, waiting_time, duration=30):
    return duration


if __name__ == "__main__":
    # quick smoke test: fixed-timer under light traffic
    result = run_simulation(fixed_timer_controller, 0.15, 0.15, duration_seconds=3600, seed=1)
    print("Fixed-timer, light traffic, 1hr sim:")
    print(f"  avg delay: {result['avg_delay_sec']:.2f}s  vehicles: {result['total_vehicles']}")
