"""Builds replay_3d.html: inlines vendored Three.js r160 + OrbitControls and both
recorded traces, so the page runs fully offline via file://. Run record_trace.py first."""
import json

html = open('replay_3d_template.html').read()
traces = json.dumps({"fixed": json.load(open('trace_fixed.json')),
                     "fuzzy_ga": json.load(open('trace_fuzzy_ga.json'))}, separators=(',', ':'))
for key, src in [('/*THREE*/', open('vendor/three.min.js').read()),
                 ('/*ORBIT*/', open('vendor/OrbitControls.js').read()),
                 ('/*TRACES*/', traces)]:
    assert key in html and '</script' not in src.lower()
    html = html.replace(key, src, 1)
open('replay_3d.html', 'w').write(html)
print(f"Wrote replay_3d.html ({len(html)/1e6:.2f} MB)")
