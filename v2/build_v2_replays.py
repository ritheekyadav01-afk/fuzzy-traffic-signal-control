"""Only meaningful if fuzzy-v2 was promoted: regenerate traces + a 3D replay from the official v2 controller into v2/ (v1 files untouched)."""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import server
p = server.parse_params({'preset': 'uneven', 'seed': '99', 'controller': 'fuzzy_v2_best'})
scn, out, summary = server.simulate_request(p)
json.dump(out['fixed']['trace'], open(os.path.join(HERE, 'trace_fixed_v2.json'), 'w'))
json.dump(out['fuzzy_ga']['trace'], open(os.path.join(HERE, 'trace_fuzzy_v2.json'), 'w'))
h, _ = server.replay_html(p)
open(os.path.join(HERE, 'replay_3d_v2.html'), 'w').write(h)
print('uneven seed 99:', {k: round(v, 2) if isinstance(v, float) else v for k, v in summary.items() if k != 'params'})
