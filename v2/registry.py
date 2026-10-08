"""Named controllers for the prototype (CLI, server).  Reads data/controllers.json (written by export_controllers.py after
training/validation selection); falls back to the hand-designed defaults so the tools always work."""
import os, sys, json
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
for p in (ROOT, HERE):
    if p not in sys.path:
        sys.path.insert(0, p)
import controllers as C
import fuzzy2

FILE = os.path.join(HERE, 'data', 'controllers.json')

DISPLAY = {'fixed_30s': 'Fixed 30 s', 'best_fixed_29s': 'Best fixed (29 s)', 'best_fixed_56s': 'Best fixed (56 s, raw-mean)',
           'actuated': 'Actuated rule', 'pressure_split': 'Pressure split', 'longest_queue_first': 'Longest-queue-first',
           'fuzzy_v1_default': 'Fuzzy v1 (default)', 'fuzzy_v1_GA_official': 'Fuzzy v1 + GA', 'fuzzy_v2_default': 'Fuzzy v2 (default)',
           'fuzzy_v2_best': 'Fuzzy v2 (trained)'}


def load():
    specs = {'fixed_30s': {'type': 'fixed', 'd': 30}, 'actuated': {'type': 'actuated', 'gain': 3.0},
             'pressure_split': {'type': 'pressure'}, 'longest_queue_first': {'type': 'lqf'},
             'fuzzy_v1_default': {'type': 'fuzzy1', 'theta': [25.0, 60.0, 35.0]},
             'fuzzy_v2_default': {'type': 'fuzzy2', 'genes': list(map(float, fuzzy2.DEFAULT_GENES))}}
    meta = {'promoted': None, 'official_v2': None}
    if os.path.exists(FILE):
        d = json.load(open(FILE))
        specs.update(d['specs']); meta = {k: d.get(k) for k in ('promoted', 'official_v2', 'note')}
        if d.get('official_v2') in d['specs']:
            specs['fuzzy_v2_best'] = d['specs'][d['official_v2']]
    else:
        r = os.path.join(ROOT, 'results.json')
        if os.path.exists(r):
            specs['fuzzy_v1_GA_official'] = {'type': 'fuzzy1', 'theta': [float(x) for x in json.load(open(r))['best_theta']]}
    return specs, meta


def build(name, specs=None):
    specs = specs or load()[0]
    return C.build(specs[name])
