"""Shared evaluation harness: cached pre-drawn arrivals (common random numbers), per-(scenario,seed) runs, normalised fitness."""
import os, sys, json
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
for p in (ROOT, HERE):
    if p not in sys.path:
        sys.path.insert(0, p)
import scenarios as S
import simulate2 as sim2
import controllers as C

SETS = S.load()                      # {'train','validation','test','legacy'} -> list of scenarios
_ARR = {}


def arrivals(scn, seed):
    k = (scn['id'], seed)
    if k not in _ARR:
        _ARR[k] = sim2.make_arrivals(scn, seed)
    return _ARR[k]


def pairs(set_name):
    """Ordered list of (scenario, seed) for a set."""
    return [(s, seed) for s in SETS[set_name] for seed in s['seeds']]


def run(ctrl, scn, seed, **kw):
    return sim2.run_simulation2(ctrl, scn, seed=seed, arrivals=arrivals(scn, seed), **kw)


def evaluate(spec_or_ctrl, set_name, keys=('avg_delay_sec',)):
    """Run a controller over every (scenario, seed) of a set. Returns {key: np.array}, order = pairs(set_name)."""
    ctrl = C.build(spec_or_ctrl) if isinstance(spec_or_ctrl, dict) else spec_or_ctrl
    out = {k: [] for k in keys}
    for scn, seed in pairs(set_name):
        r = run(ctrl, scn, seed)
        for k in keys:
            out[k].append(r[k])
    return {k: np.array(v) for k, v in out.items()}


def per_scenario(arr, set_name):
    """Average the per-seed values of each scenario -> one value per scenario (paired unit of analysis)."""
    sizes = [len(s['seeds']) for s in SETS[set_name]]
    idx = np.cumsum([0] + sizes)
    return np.array([arr[idx[i]:idx[i + 1]].mean() for i in range(len(sizes))])
