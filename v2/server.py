#!/usr/bin/env python3
"""
Local prototype server (standard library only, works offline).

   /usr/bin/python3 v2/server.py [--port 8000]      then open  http://localhost:8000

The browser only displays: every simulation / fuzzy computation runs here, in Python, using the same code that produced
the reported results (simulate2.py + controllers).  The 3D replay is the v1 viewer (unchanged JS) fed with traces
recorded by the real simulator for the scenario and controller you pick.

Routes
  GET  /                       form (demand profile / rates / controller / seed)
  GET  /replay?...             runs the simulation, returns the 3D replay page (fixed-30 vs chosen controller)
  POST /api/simulate           JSON {ns, ew, profile, profile_seed, seed, controller} -> summary + both traces
  GET  /api/predict?queue=&wait=&opp=   explainable fuzzy-v2 green-time recommendation (rules fired)
  GET  /api/controllers        available controllers
"""
import os, sys, json, argparse, html
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE); sys.path.insert(0, ROOT)
import numpy as np
import scenarios as S
import simulate2 as sim2
import controllers as C
import registry
import predict as P
import fuzzy2

PROFILES = ['constant', 'rush_ramp', 'surge', 'one_sided_surge', 'lull', 'balanced_then_skewed']
PRESETS = dict(S.LEGACY)
_SPECS, _META = registry.load()
_BASE = {}


def _template():
    if 'html' not in _BASE:
        t = open(os.path.join(ROOT, 'replay_3d_template.html')).read()
        for key, path in (('/*THREE*/', 'vendor/three.min.js'), ('/*ORBIT*/', 'vendor/OrbitControls.js')):
            t = t.replace(key, open(os.path.join(ROOT, path)).read(), 1)
        _BASE['html'] = t
    return _BASE['html']


def parse_params(q):
    """Validate + normalise request parameters (works for GET query dicts and POST JSON)."""
    g = lambda k, d=None: (q.get(k, [d])[0] if isinstance(q.get(k), list) else q.get(k, d))
    preset = g('preset', 'custom')
    if preset in PRESETS:
        ns, ew = PRESETS[preset]; profile = 'constant'
    else:
        ns, ew = float(g('ns', 0.35)), float(g('ew', 0.10)); profile = g('profile', 'constant')
    if profile not in PROFILES:
        raise ValueError('unknown profile')
    ns = min(max(ns, 0.0), 0.6); ew = min(max(ew, 0.0), 0.6)
    ctrl = g('controller', 'fuzzy_v2_best' if 'fuzzy_v2_best' in _SPECS else 'fuzzy_v2_default')
    if ctrl not in _SPECS:
        raise ValueError('unknown controller: ' + str(ctrl))
    return {'preset': preset, 'ns': ns, 'ew': ew, 'profile': profile, 'profile_seed': int(g('profile_seed', 1)), 'seed': int(g('seed', 1)), 'controller': ctrl}


def make_scenario(p):
    if p['profile'] == 'constant':
        return S.scenario_from_rates(p['ns'], p['ew'], name=p['preset'] if p['preset'] != 'custom' else 'custom')
    knots, params = S.make_profile(p['profile'], np.random.default_rng(p['profile_seed']))
    return {'id': 'live', 'name': p['profile'], 'profile': p['profile'], 'params': params, 'duration': S.DURATION,
            'knots': [[float(a), float(b), float(c)] for a, b, c in knots], 'seeds': [p['seed']]}


def simulate_request(p):
    scn = make_scenario(p)
    arr = sim2.make_arrivals(scn, p['seed'])        # identical traffic for both controllers
    out = {}
    for key, name in (('fixed', 'fixed_30s'), ('fuzzy_ga', p['controller'])):
        tr = []
        r = sim2.run_simulation2(C.build(_SPECS[name]), scn, seed=p['seed'], arrivals=arr, trace=tr)
        out[key] = {'trace': tr, 'result': {k: r[k] for k in ('avg_delay_sec', 'total_vehicles', 'p95_queue', 'max_queue', 'worst_dir_delay_sec', 'served_total')}}
    f, c = out['fixed']['result']['avg_delay_sec'], out['fuzzy_ga']['result']['avg_delay_sec']
    return scn, out, {'fixed_30s_avg_delay_s': f, 'controller': p['controller'], 'controller_avg_delay_s': c,
                      'improvement_pct': (f - c) / f * 100 if f else 0.0, 'scenario': scn['name'], 'params': p,
                      'note': 'single seed; one run is an illustration, not evidence (see RESULTS.md for the 60-scenario test)'}


def replay_html(p):
    scn, out, summary = simulate_request(p)
    disp = registry.DISPLAY.get(p['controller'], p['controller'])
    desc = f"{scn['name']} · NS/EW rates {scn['knots'][0][1]:.2f}/{scn['knots'][0][2]:.2f} → {'time-varying' if scn['profile'] != 'constant' else 'constant'} · seed {p['seed']}"
    h = _template().replace('/*TRACES*/', json.dumps({'fixed': out['fixed']['trace'], 'fuzzy_ga': out['fuzzy_ga']['trace']}, separators=(',', ':')), 1)
    h = h.replace('Fuzzy + GA', disp).replace('Fuzzy+GA', disp)
    h = h.replace('scenario: uneven · NS 0.35/s · EW 0.10/s · pre-recorded trace replay', html.escape(desc) + ' · server-side simulation')
    h = h.replace('<title>Traffic Replay 3D</title>', '<title>Traffic Replay (live)</title>')
    back = '<a href="/" style="position:fixed;left:16px;bottom:96px;color:#60a5fa;font:12px ui-monospace,monospace">← new run</a>'
    return h.replace('</body>', back + '</body>', 1), summary


INDEX = """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Traffic Controller Lab</title><style>
:root{--bg:#05070c;--panel:#0d121f;--line:#1b2436;--blue:#3b82f6;--blue-bright:#60a5fa;--cyan:#22d3ee;--green:#34d399;--text:#e7ecf5;--text-dim:#8b96ab;--mono:ui-monospace,"SF Mono",Menlo,monospace}
body{margin:0;background:var(--bg);color:var(--text);font-family:system-ui,sans-serif;display:flex;justify-content:center;padding:32px 16px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:24px;max-width:560px;width:100%}
h1{margin:0 0 4px;font-size:22px}p.sub{margin:0 0 20px;color:var(--text-dim);font:12px var(--mono)}
label{display:block;margin:14px 0 4px;color:var(--text-dim);font:12px var(--mono)}
input,select{width:100%;box-sizing:border-box;background:var(--bg);color:var(--text);border:1px solid var(--line);border-radius:8px;padding:10px;font:14px var(--mono)}
button{margin-top:22px;width:100%;background:var(--blue);color:#fff;border:0;border-radius:8px;padding:12px;font:600 14px var(--mono);cursor:pointer}
button:hover{background:var(--blue-bright)}.row{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.note{margin-top:18px;color:var(--text-dim);font:11px/1.6 var(--mono)}code{color:var(--cyan)}
</style></head><body><form class="card" action="/replay" method="get">
<h1>Traffic Controller Lab</h1><p class="sub">real Python simulation, server-side · no JavaScript traffic math</p>
<label>Preset scenario (overrides rates / profile)</label>
<select name="preset"><option value="custom">custom (use fields below)</option>__PRESETS__</select>
<div class="row"><div><label>NS arrival rate (veh/s, 0-0.6)</label><input name="ns" value="0.35" type="number" step="0.01" min="0" max="0.6"></div>
<div><label>EW arrival rate (veh/s, 0-0.6)</label><input name="ew" value="0.10" type="number" step="0.01" min="0" max="0.6"></div></div>
<label>Demand profile</label><select name="profile">__PROFILES__</select>
<div class="row"><div><label>Profile seed (shape of non-constant profiles)</label><input name="profile_seed" value="1" type="number"></div>
<div><label>Traffic seed (random arrivals)</label><input name="seed" value="1" type="number"></div></div>
<label>Controller to compare against fixed-30 s</label><select name="controller">__CONTROLLERS__</select>
<button type="submit">Run simulation &amp; open 3D replay</button>
<div class="note">Everything on the next page is a replay of what the Python simulator recorded. Use the toggle to switch controllers at the same simulated second.<br>
Other endpoints: <code>/api/predict?queue=30&amp;wait=60&amp;opp=8</code> · <code>/api/controllers</code> · <code>POST /api/simulate</code></div></form></body></html>"""


def index_html():
    pre = ''.join(f'<option value="{k}">{k} ({v[0]}/{v[1]})</option>' for k, v in PRESETS.items())
    prof = ''.join(f'<option value="{k}">{k}</option>' for k in PROFILES)
    default = 'fuzzy_v2_best' if 'fuzzy_v2_best' in _SPECS else 'fuzzy_v2_default'
    ctr = ''.join(f'<option value="{k}"{" selected" if k == default else ""}>{html.escape(registry.DISPLAY.get(k, k))}</option>' for k in _SPECS if k != 'fixed_30s')
    return INDEX.replace('__PRESETS__', pre).replace('__PROFILES__', prof).replace('__CONTROLLERS__', ctr)


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype='text/html; charset=utf-8'):
        b = body.encode() if isinstance(body, str) else body
        self.send_response(code); self.send_header('Content-Type', ctype); self.send_header('Content-Length', str(len(b)))
        self.send_header('Cache-Control', 'no-store'); self.end_headers(); self.wfile.write(b)

    def _json(self, code, obj):
        self._send(code, json.dumps(obj), 'application/json')

    def do_GET(self):
        u = urlparse(self.path); q = parse_qs(u.query)
        try:
            if u.path == '/':
                self._send(200, index_html())
            elif u.path == '/replay':
                h, _ = replay_html(parse_params(q)); self._send(200, h)
            elif u.path == '/api/predict':
                spec = _SPECS.get('fuzzy_v2_best', _SPECS['fuzzy_v2_default'])
                f = fuzzy2.Fuzzy2(np.asarray(spec['genes'], float))
                self._json(200, P.explain(f, float(q['queue'][0]), float(q['wait'][0]), float(q['opp'][0])))
            elif u.path == '/api/controllers':
                self._json(200, {'controllers': list(_SPECS), 'meta': _META})
            elif u.path == '/healthz':
                self._send(200, 'ok', 'text/plain')
            else:
                self._send(404, 'not found', 'text/plain')
        except (ValueError, KeyError) as e:
            self._json(400, {'error': str(e)})

    def do_POST(self):
        if urlparse(self.path).path != '/api/simulate':
            return self._send(404, 'not found', 'text/plain')
        try:
            n = int(self.headers.get('Content-Length', 0))
            p = parse_params(json.loads(self.rfile.read(n) or b'{}'))
            _, out, summary = simulate_request(p)
            self._json(200, {'summary': summary, 'fixed_30s': out['fixed'], 'controller': out['fuzzy_ga']})
        except (ValueError, KeyError, json.JSONDecodeError) as e:
            self._json(400, {'error': str(e)})

    def log_message(self, fmt, *a):
        sys.stderr.write('[server] ' + fmt % a + '\n')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--port', type=int, default=8000); ap.add_argument('--host', default='127.0.0.1')
    a = ap.parse_args()
    srv = ThreadingHTTPServer((a.host, a.port), Handler)
    print(f"Traffic Controller Lab on http://localhost:{a.port}   (Ctrl+C to stop)")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print('\nstopped')


if __name__ == '__main__':
    main()
