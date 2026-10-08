"""
Phase 3 - simulate2: additive extension of v1's simulate.py (which is NOT modified).

Same core model as v1 (1 s steps, Poisson arrivals, 2 phases NS/EW strictly alternating, saturation flow 0.5 veh/s,
3 s clearance, green clipped to [10, 60]) and the same delay definition
(sum over seconds of vehicles queued / vehicles arrived), plus:
  * time-varying arrival rates (scenario knots from scenarios.py)
  * per-direction delay, throughput, p95 / max queue, worst-direction delay (fairness)
  * optional `on_tick` hook identical to v1's and an optional `trace` list (v1 trace format + exact departed_ns/ew)
  * controllers may take the OPPOSING queue as an optional 3rd argument
  * arrivals can be pre-drawn (`make_arrivals`) and shared between controllers (common random numbers).
    The v1 RNG consumes exactly 2 Poisson draws per simulated second regardless of the controller, so a
    bulk draw with interleaved NS/EW rates reproduces v1's stream exactly (verified in tests).
"""
import inspect
import numpy as np
from scenarios import rate_arrays, scenario_from_rates

SATURATION_FLOW_PER_SEC = 0.5
CLEARANCE_SECONDS = 3
MIN_GREEN = 10
MAX_GREEN = 60


def wants_opposing(fn):
    """True if controller_fn takes (queue, waiting_time, opposing_queue)."""
    flag = getattr(fn, 'wants_opposing', None)
    if flag is not None:
        return bool(flag)
    try:
        params = inspect.signature(fn).parameters.values()
    except (TypeError, ValueError):
        return False
    required = [p for p in params if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD) and p.default is p.empty]
    return len(required) >= 3 or any(p.kind == p.VAR_POSITIONAL for p in params)


def make_arrivals(scenario, seed):
    """Pre-draw the integer arrivals per second (NS, EW) exactly as v1's per-second rng.poisson calls would."""
    r_ns, r_ew = rate_arrays(scenario)
    lam = np.empty(2 * len(r_ns))
    lam[0::2] = r_ns
    lam[1::2] = r_ew
    draws = np.random.default_rng(seed).poisson(lam)
    return draws[0::2].astype(np.int64), draws[1::2].astype(np.int64)


def run_simulation2(controller_fn, scenario=None, seed=0, arrivals=None, rate_ns=None, rate_ew=None,
                    duration_seconds=3600, on_tick=None, trace=None):
    if scenario is None:
        scenario = scenario_from_rates(rate_ns, rate_ew, duration_seconds)
    T = int(scenario['duration'])
    an, ae = arrivals if arrivals is not None else make_arrivals(scenario, seed)
    an = an.tolist(); ae = ae.tolist()
    opp = wants_opposing(controller_fn)

    q = {'NS': 0.0, 'EW': 0.0}
    since = {'NS': 0.0, 'EW': 0.0}
    tot_delay = d_ns = d_ew = 0.0
    arr_ns = arr_ew = 0
    srv = {'NS': 0.0, 'EW': 0.0}
    qtot = np.empty(T)
    qmax_dir = 0.0
    t = 0
    cur = 'NS'

    def tick(phase):
        nonlocal tot_delay, d_ns, d_ew, qmax_dir
        s = q['NS'] + q['EW']
        tot_delay += s
        d_ns += q['NS']; d_ew += q['EW']
        qtot[t - 1] = s
        if q['NS'] > qmax_dir: qmax_dir = q['NS']
        if q['EW'] > qmax_dir: qmax_dir = q['EW']
        if on_tick:
            on_tick(t, q['NS'], q['EW'], phase, tot_delay)
        if trace is not None:
            trace.append({"t": t, "queue_ns": round(q['NS'], 3), "queue_ew": round(q['EW'], 3), "phase": phase,
                          "cumulative_delay": round(tot_delay, 3),
                          "departed_ns": round(srv['NS'], 3), "departed_ew": round(srv['EW'], 3)})

    while t < T:
        other = 'EW' if cur == 'NS' else 'NS'
        green = controller_fn(q[cur], since[cur], q[other]) if opp else controller_fn(q[cur], since[cur])
        green = max(MIN_GREEN, min(MAX_GREEN, green))
        for _ in range(int(round(green))):
            if t >= T:
                break
            q['NS'] += an[t]; q['EW'] += ae[t]
            arr_ns += an[t]; arr_ew += ae[t]
            served = min(q[cur], SATURATION_FLOW_PER_SEC)
            q[cur] -= served
            srv[cur] += served
            since[other] += 1
            t += 1
            tick(cur)
        for _ in range(CLEARANCE_SECONDS):
            if t >= T:
                break
            q['NS'] += an[t]; q['EW'] += ae[t]
            arr_ns += an[t]; arr_ew += ae[t]
            since['NS'] += 1; since['EW'] += 1
            t += 1
            tick('clearance')
        since[cur] = 0
        cur = other

    arrived = arr_ns + arr_ew
    dly_ns = d_ns / arr_ns if arr_ns else 0.0
    dly_ew = d_ew / arr_ew if arr_ew else 0.0
    return {
        'avg_delay_sec': tot_delay / arrived if arrived else 0.0,
        'total_vehicles': arrived,
        'final_queue_ns': q['NS'], 'final_queue_ew': q['EW'],
        'delay_ns_sec': dly_ns, 'delay_ew_sec': dly_ew,
        'worst_dir_delay_sec': max(dly_ns, dly_ew),
        'p95_queue': float(np.percentile(qtot, 95)), 'max_queue': float(qtot.max()), 'max_queue_dir': qmax_dir,
        'served_total': srv['NS'] + srv['EW'], 'served_ns': srv['NS'], 'served_ew': srv['EW'],
        'arrived_ns': arr_ns, 'arrived_ew': arr_ew,
    }
