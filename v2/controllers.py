"""All controllers (Phase 2 baselines + fuzzy-v1 + fuzzy-v2) behind one spec -> controller_fn builder.
Every controller conforms to controller_fn(queue, waiting_time[, opposing_queue]) -> green seconds."""
import os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
for p in (ROOT, HERE):
    if p not in sys.path:
        sys.path.insert(0, p)
import fuzzy_core as v1
from fuzzy2 import Fuzzy2


# ---------- Phase 2 baselines ----------
def fixed(duration):
    def ctrl(queue, waiting_time):
        return duration
    ctrl.wants_opposing = False
    return ctrl


def actuated(gain):
    """Green proportional to own queue (gain seconds per queued vehicle), clipped 10-60 s.
    gain=2 clears exactly the queue present at the start of green (service rate 0.5 veh/s)."""
    def ctrl(queue, waiting_time):
        return min(60.0, max(10.0, gain * queue))
    ctrl.wants_opposing = False
    return ctrl


def pressure_split():
    """Max-pressure-style: split a 70 s budget between the two phases in proportion to queue share, clipped 10-60."""
    def ctrl(queue, waiting_time, opposing_queue):
        tot = queue + opposing_queue
        if tot <= 0:
            return 30.0
        return min(60.0, max(10.0, 70.0 * queue / tot))
    ctrl.wants_opposing = True
    return ctrl


def longest_queue_first():
    """Bang-bang: the longer queue gets the maximum green, the shorter the minimum."""
    def ctrl(queue, waiting_time, opposing_queue):
        return 60.0 if queue >= opposing_queue else 10.0
    ctrl.wants_opposing = True
    return ctrl


# ---------- fuzzy-v1 (unchanged maths, faster plumbing) ----------
def fuzzy_v1(theta):
    """Exactly v1's green_duration (same membership/rule code), with the 3 output-set shapes cached per theta."""
    c_q, c_w, c_g = theta
    shapes = {lab: np.array([v1._tri(x, *v1._green_shape(lab, c_g)) for x in v1.GREEN_UNIVERSE]) for lab in ('short', 'medium', 'long')}
    U = v1.GREEN_UNIVERSE

    def ctrl(queue, waiting_time):
        queue = max(v1.QUEUE_DOMAIN[0], min(v1.QUEUE_DOMAIN[1], queue))
        waiting_time = max(v1.WAIT_DOMAIN[0], min(v1.WAIT_DOMAIN[1], waiting_time))
        ql, qm, qh = v1._memberships(queue, *v1.QUEUE_DOMAIN, c_q)
        ws, wm, wl = v1._memberships(waiting_time, *v1.WAIT_DOMAIN, c_w)
        queue_m = {'low': ql, 'medium': qm, 'high': qh}
        wait_m = {'short': ws, 'moderate': wm, 'long': wl}
        out = {'short': 0.0, 'medium': 0.0, 'long': 0.0}
        for q_label, w_label, o_label in v1.RULES:
            s = min(queue_m[q_label], wait_m[w_label])
            out[o_label] = max(out[o_label], s)
        agg = np.zeros(len(U))
        for lab, s in out.items():
            agg = np.maximum(agg, np.minimum(shapes[lab], s))
        if agg.sum() == 0:
            return float(np.mean(U))
        return float(np.sum(U * agg) / np.sum(agg))
    ctrl.wants_opposing = False
    return ctrl


def build(spec):
    """spec: {'type': 'fixed', 'd': 30} | actuated gain | pressure | lqf | fuzzy1 theta | fuzzy2 genes (+weights)"""
    t = spec['type']
    if t == 'fixed':
        return fixed(spec['d'])
    if t == 'actuated':
        return actuated(spec['gain'])
    if t == 'pressure':
        return pressure_split()
    if t == 'lqf':
        return longest_queue_first()
    if t == 'fuzzy1':
        return fuzzy_v1(spec['theta'])
    if t == 'fuzzy2':
        return Fuzzy2(np.asarray(spec['genes'], float))
    raise ValueError(t)
