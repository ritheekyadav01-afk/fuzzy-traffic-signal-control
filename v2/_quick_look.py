import os, sys, json, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import harness as H
bf = H.evaluate({'type':'fixed','d':29}, 'train')['avg_delay_sec']
bfv = H.evaluate({'type':'fixed','d':29}, 'validation')['avg_delay_sec']
th = [32.784, 30.785, 52.154]
specs = {'fixed30': {'type':'fixed','d':30}, 'fixed29': {'type':'fixed','d':29}, 'fixed56': {'type':'fixed','d':56},
 'actuated3.0': {'type':'actuated','gain':3.0}, 'actuated2.0': {'type':'actuated','gain':2.0}, 'pressure': {'type':'pressure'}, 'lqf': {'type':'lqf'},
 'fuzzy1_default': {'type':'fuzzy1','theta':[25,60,35]}, 'fuzzy1_ga(v1 official)': {'type':'fuzzy1','theta':th},
 'fuzzy2_default': {'type':'fuzzy2','genes':H.C.Fuzzy2 and list(__import__('fuzzy2').DEFAULT_GENES)}}
print(f"{'controller':<24}{'TRAIN ratio':>12}{'TRAIN raw':>10}{'VAL ratio':>11}{'VAL raw':>9}{'ms/sim':>8}")
for n, s in specs.items():
    t0 = time.time(); a = H.evaluate(s, 'train')['avg_delay_sec']; dt = (time.time()-t0)/len(a)*1000
    b = H.evaluate(s, 'validation')['avg_delay_sec']
    print(f"{n:<24}{(a/bf).mean():>12.3f}{a.mean():>10.1f}{(b/bfv).mean():>11.3f}{b.mean():>9.1f}{dt:>8.1f}")
