"""
Phase 1 - parametric scenario generator + disjoint TRAIN / VALIDATION / TEST sets.

A scenario is JSON-serialisable: {"id","name","profile","duration","knots":[[t,rate_ns,rate_ew],...],"seeds":[...]}.
Per-second arrival rates are the piecewise-linear interpolation of the knots (a surge is two knots 1 s apart).
All rates are clipped to [RATE_MIN, RATE_MAX] = [0.03, 0.40] veh/s per direction.
"""
import os, json
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, 'data')
SCEN_FILE = os.path.join(DATA, 'scenarios.json')
RATE_MIN, RATE_MAX = 0.03, 0.40
DURATION = 3600

# fixed, recorded generator seeds (documented in FINAL_REPORT)
SET_SEEDS = {'train': 1001, 'validation': 2002, 'test': 3003}
SET_SIZES = {'train': 40, 'validation': 20, 'test': 60}
# simulation (traffic-draw) seeds per scenario; disjoint ranges per set
SIM_SEEDS = {'train': (7, 17, 27), 'validation': (101, 102, 103), 'test': None}  # test: 3 fresh seeds per scenario (below)
PROFILES = ['constant', 'constant', 'rush_ramp', 'surge', 'one_sided_surge', 'lull', 'balanced_then_skewed']

LEGACY = {'light': (0.10, 0.10), 'moderate': (0.20, 0.20), 'uneven': (0.35, 0.10),
          'rush_hour': (0.26, 0.19), 'heavy': (0.30, 0.30)}
LEGACY_SEED = 99


def _c(x):
    return float(np.clip(x, RATE_MIN, RATE_MAX))


def make_profile(kind, rng, T=DURATION):
    """Return (knots, params) for one profile kind."""
    u = lambda a, b: float(rng.uniform(a, b))
    if kind == 'constant':
        a, b = u(RATE_MIN, RATE_MAX), u(RATE_MIN, RATE_MAX)
        return [[0, _c(a), _c(b)], [T, _c(a), _c(b)]], {'ns': a, 'ew': b}
    if kind == 'rush_ramp':          # ramp up to a peak around the middle, then back down
        base_ns, base_ew = u(0.04, 0.12), u(0.04, 0.12)
        peak_ns, peak_ew = u(0.15, 0.40), u(0.10, 0.35)
        tp = u(0.35, 0.65) * T
        k = [[0, base_ns, base_ew], [tp, peak_ns, peak_ew], [T, base_ns, base_ew]]
        return [[t, _c(a), _c(b)] for t, a, b in k], {'peak_ns': peak_ns, 'peak_ew': peak_ew, 'tpeak': tp}
    if kind == 'surge':              # sudden surge in both directions
        base_ns, base_ew = u(0.05, 0.15), u(0.05, 0.15)
        f = u(1.8, 3.0); t0 = u(0.2, 0.5) * T; dur = u(0.15, 0.35) * T
        hi_ns, hi_ew = base_ns * f, base_ew * f
        k = [[0, base_ns, base_ew], [t0, base_ns, base_ew], [t0 + 1, hi_ns, hi_ew], [t0 + dur, hi_ns, hi_ew],
             [t0 + dur + 1, base_ns, base_ew], [T, base_ns, base_ew]]
        return [[t, _c(a), _c(b)] for t, a, b in k], {'factor': f, 't0': t0, 'dur': dur}
    if kind == 'one_sided_surge':    # only one direction surges
        base_ns, base_ew = u(0.06, 0.14), u(0.06, 0.14)
        side = int(rng.integers(0, 2)); hi = u(0.25, 0.40)
        t0 = u(0.2, 0.5) * T; dur = u(0.15, 0.35) * T
        hn, he = (hi, base_ew) if side == 0 else (base_ns, hi)
        k = [[0, base_ns, base_ew], [t0, base_ns, base_ew], [t0 + 1, hn, he], [t0 + dur, hn, he],
             [t0 + dur + 1, base_ns, base_ew], [T, base_ns, base_ew]]
        return [[t, _c(a), _c(b)] for t, a, b in k], {'surge_side': 'NS' if side == 0 else 'EW', 'rate': hi, 't0': t0, 'dur': dur}
    if kind == 'lull':               # off-peak: low demand with a slight bump
        a, b = u(0.03, 0.09), u(0.03, 0.09)
        bump = u(1.0, 1.6); tb = u(0.3, 0.7) * T
        k = [[0, a, b], [tb, a * bump, b * bump], [T, a, b]]
        return [[t, _c(x), _c(y)] for t, x, y in k], {'ns': a, 'ew': b, 'bump': bump}
    if kind == 'balanced_then_skewed':  # equal demand first, then one direction dominates
        m = u(0.10, 0.22); skew_ns = int(rng.integers(0, 2)); ts = u(0.4, 0.6) * T
        hi, lo = u(0.28, 0.40), u(0.04, 0.10)
        hn, le = (hi, lo) if skew_ns else (lo, hi)
        k = [[0, m, m], [ts, m, m], [ts + 1, hn, le], [T, hn, le]]
        return [[t, _c(a), _c(b)] for t, a, b in k], {'balanced': m, 'skew': 'NS' if skew_ns else 'EW', 'tskew': ts}
    raise ValueError(kind)


def generate_set(name, n, gen_seed, sim_seeds=None):
    rng = np.random.default_rng(gen_seed)
    out = []
    for i in range(n):
        kind = PROFILES[i % len(PROFILES)]
        knots, params = make_profile(kind, rng)
        seeds = list(sim_seeds) if sim_seeds else [int(s) for s in rng.integers(10_000, 10_000_000, size=3)]
        out.append({'id': f'{name}_{i:02d}', 'name': f'{name}_{i:02d}_{kind}', 'profile': kind, 'params': params,
                    'duration': DURATION, 'knots': [[float(a), float(b), float(c)] for a, b, c in knots], 'seeds': seeds})
    # shuffle order deterministically so profile kinds are interleaved but set sizes stay fixed
    return out


def legacy_scenarios():
    return [{'id': f'legacy_{k}', 'name': k, 'profile': 'constant', 'params': {'ns': a, 'ew': b}, 'duration': DURATION,
             'knots': [[0.0, a, b], [float(DURATION), a, b]], 'seeds': [LEGACY_SEED]} for k, (a, b) in LEGACY.items()]


def build_all():
    sets = {}
    for name in ('train', 'validation', 'test'):
        sets[name] = generate_set(name, SET_SIZES[name], SET_SEEDS[name], SIM_SEEDS[name])
    sets['legacy'] = legacy_scenarios()
    # disjointness check: no identical knot tables across train/validation/test, and no shared sim seeds in test
    sig = lambda s: tuple(round(v, 6) for k in s['knots'] for v in k)
    seen = {}
    for name in ('train', 'validation', 'test'):
        for s in sets[name]:
            assert sig(s) not in seen, f"duplicate scenario between {seen.get(sig(s))} and {name}"
            seen[sig(s)] = name
    train_seeds = set(SIM_SEEDS['train']) | set(SIM_SEEDS['validation'])
    for s in sets['test']:
        assert not (set(s['seeds']) & train_seeds)
    return {'meta': {'generator_seeds': SET_SEEDS, 'sizes': SET_SIZES, 'rate_range': [RATE_MIN, RATE_MAX],
                     'duration_s': DURATION, 'profiles': sorted(set(PROFILES)), 'legacy_seed': LEGACY_SEED}, 'sets': sets}


def save():
    os.makedirs(DATA, exist_ok=True)
    d = build_all()
    json.dump(d, open(SCEN_FILE, 'w'), indent=1)
    return d


def load():
    if not os.path.exists(SCEN_FILE):
        save()
    return json.load(open(SCEN_FILE))['sets']


def rate_arrays(scn):
    """Per-second (rate_ns, rate_ew) arrays of length `duration` (second index t = 0..duration-1)."""
    k = np.array(scn['knots'], dtype=float)
    t = np.arange(scn['duration'], dtype=float)
    return np.interp(t, k[:, 0], k[:, 1]), np.interp(t, k[:, 0], k[:, 2])


def scenario_from_rates(ns, ew, duration=DURATION, name='custom'):
    return {'id': name, 'name': name, 'profile': 'constant', 'params': {'ns': ns, 'ew': ew}, 'duration': duration,
            'knots': [[0.0, ns, ew], [float(duration), ns, ew]], 'seeds': [0]}


if __name__ == '__main__':
    d = save()
    for k, v in d['sets'].items():
        kinds = {}
        for s in v: kinds[s['profile']] = kinds.get(s['profile'], 0) + 1
        print(k, len(v), kinds)
