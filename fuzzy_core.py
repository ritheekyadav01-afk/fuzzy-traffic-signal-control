"""
fuzzy_core.py
-------------
A GA-tunable Mamdani fuzzy controller for traffic signal green-duration.

Design: each input/output variable uses a 3-term "movable partition" —
low, medium, high — where ONLY the center of "medium" is a free parameter.
    low    = triangle(domain_lo, domain_lo, center)
    medium = triangle(domain_lo, center, domain_hi)
    high   = triangle(center, domain_hi, domain_hi)

This guarantees a valid fuzzy partition for any center strictly inside the
domain, and gives the GA exactly 3 numbers to tune:
    theta = (center_queue, center_wait, center_green)

Domains (fixed, matching the Phase 1 controller):
    queue_length  : 0-50 vehicles
    waiting_time  : 0-120 seconds
    green_duration: 10-60 seconds

Default theta = (25, 60, 35) reproduces the original Phase 1 hand-tuned
design's medium apexes.
"""

import numpy as np

QUEUE_DOMAIN = (0, 50)
WAIT_DOMAIN = (0, 120)
GREEN_DOMAIN = (10, 60)

DEFAULT_THETA = (25.0, 60.0, 35.0)

GREEN_UNIVERSE = np.arange(GREEN_DOMAIN[0], GREEN_DOMAIN[1] + 1, 1)

RULES = [
    ('low', 'short', 'short'),
    ('low', 'moderate', 'short'),
    ('low', 'long', 'medium'),
    ('medium', 'short', 'medium'),
    ('medium', 'moderate', 'medium'),
    ('medium', 'long', 'long'),
    ('high', 'short', 'medium'),
    ('high', 'moderate', 'long'),
    ('high', 'long', 'long'),
]


def _tri(x, a, b, c):
    """Triangular membership of scalar x for triangle (a,b,c)."""
    if a == b:
        left = 1.0 if x <= a else 0.0
    else:
        left = (x - a) / (b - a)
    if b == c:
        right = 1.0 if x >= c else 0.0
    else:
        right = (c - x) / (c - b)
    return max(0.0, min(left if x <= b else right, 1.0)) if a <= x <= c or x == b else 0.0


def _memberships(x, domain_lo, domain_hi, center):
    """Return {low, medium/moderate-ish, high} memberships for one movable partition."""
    low = _tri(x, domain_lo, domain_lo, center)
    mid = _tri(x, domain_lo, center, domain_hi)
    high = _tri(x, center, domain_hi, domain_hi)
    return low, mid, high


def _green_shape(label, center):
    """Triangle (a,b,c) for a green_duration fuzzy set, given movable center."""
    lo, hi = GREEN_DOMAIN
    if label == 'short':
        return (lo, lo, center)
    if label == 'medium':
        return (lo, center, hi)
    return (center, hi, hi)  # 'long'


def green_duration(queue, waiting_time, theta=DEFAULT_THETA):
    """
    Run the Mamdani fuzzy controller for one reading.
    queue: vehicles waiting (0-50)
    waiting_time: seconds since this direction last had green (0-120)
    theta: (center_queue, center_wait, center_green) — GA-tunable
    Returns: green duration in seconds (10-60)
    """
    c_q, c_w, c_g = theta
    queue = max(QUEUE_DOMAIN[0], min(QUEUE_DOMAIN[1], queue))
    waiting_time = max(WAIT_DOMAIN[0], min(WAIT_DOMAIN[1], waiting_time))

    q_low, q_med, q_high = _memberships(queue, *QUEUE_DOMAIN, c_q)
    w_short, w_mod, w_long = _memberships(waiting_time, *WAIT_DOMAIN, c_w)

    queue_m = {'low': q_low, 'medium': q_med, 'high': q_high}
    wait_m = {'short': w_short, 'moderate': w_mod, 'long': w_long}

    output_strength = {'short': 0.0, 'medium': 0.0, 'long': 0.0}
    for q_label, w_label, out_label in RULES:
        strength = min(queue_m[q_label], wait_m[w_label])
        output_strength[out_label] = max(output_strength[out_label], strength)

    aggregated = np.zeros_like(GREEN_UNIVERSE, dtype=float)
    for out_label, strength in output_strength.items():
        a, b, c = _green_shape(out_label, c_g)
        shape = np.array([_tri(x, a, b, c) for x in GREEN_UNIVERSE])
        clipped = np.minimum(shape, strength)
        aggregated = np.maximum(aggregated, clipped)

    if aggregated.sum() == 0:
        return float(np.mean(GREEN_UNIVERSE))
    return float(np.sum(GREEN_UNIVERSE * aggregated) / np.sum(aggregated))


if __name__ == "__main__":
    # sanity check against the Phase 1 test cases
    tests = [(5, 10), (25, 50), (45, 100), (10, 90)]
    print("Default theta:", DEFAULT_THETA)
    for q, w in tests:
        print(f"  queue={q:2d} wait={w:3d} -> green={green_duration(q, w):.2f}s")
