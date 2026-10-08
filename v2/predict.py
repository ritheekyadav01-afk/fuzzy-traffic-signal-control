#!/usr/bin/env python3
"""Explainable green-time recommendation.
   /usr/bin/python3 v2/predict.py --queue 30 --wait 60 --opp 8
   /usr/bin/python3 v2/predict.py --queue 30 --wait 60 --opp 8 --controller v2-default --json
Prints the recommended green duration, the fuzzified inputs, and the rules that fired (strongest first)."""
import os, sys, json, argparse
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np
import fuzzy2
import registry


def explain(f, q, w, o, top=6):
    mq, mw, mo = f.memberships(q, w, o)
    strengths, out = f.fire(q, w, o)
    green_raw = f(q, w, o)
    fired = sorted(((s, r) for r, s in enumerate(strengths) if s > 1e-9), reverse=True)
    rules = [{'rule': f"R{r+1:02d}", 'strength': round(float(s), 4),
              'text': "IF own_queue is {} AND waiting is {} AND opposing_queue is {} THEN green is {}".format(*fuzzy2.RULES2[r]),
              'rule_weight': round(float(f.w[r]), 3)} for s, r in fired[:top]]
    return {'inputs': {'own_queue': q, 'waiting_s': w, 'opposing_queue': o},
            'memberships': {'own_queue': dict(zip(fuzzy2.Q_LABELS, map(lambda x: round(float(x), 3), mq))),
                            'waiting': dict(zip(fuzzy2.W_LABELS, map(lambda x: round(float(x), 3), mw))),
                            'opposing_queue': dict(zip(fuzzy2.O_LABELS, map(lambda x: round(float(x), 3), mo)))},
            'output_strength': dict(zip(fuzzy2.G_LABELS, map(lambda x: round(float(x), 4), out))),
            'rules_fired': rules, 'n_rules_fired': len(fired),
            'green_defuzzified_s': round(float(green_raw), 2), 'green_recommended_s': round(float(min(60.0, max(10.0, green_raw))), 1)}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--queue', type=float, required=True, help='vehicles waiting on the approach about to get green')
    ap.add_argument('--wait', type=float, required=True, help='seconds since this approach last had green')
    ap.add_argument('--opp', type=float, required=True, help='vehicles waiting on the opposing approach')
    ap.add_argument('--controller', default='v2', choices=['v2', 'v2-default'], help='v2 = trained fuzzy-v2 (validation-selected); v2-default = hand-designed')
    ap.add_argument('--json', action='store_true')
    a = ap.parse_args(argv)
    specs, meta = registry.load()
    spec = specs['fuzzy_v2_best'] if (a.controller == 'v2' and 'fuzzy_v2_best' in specs) else specs['fuzzy_v2_default']
    f = fuzzy2.Fuzzy2(np.asarray(spec['genes'], float))
    e = explain(f, a.queue, a.wait, a.opp)
    e['controller'] = 'fuzzy-v2 (trained)' if spec is specs.get('fuzzy_v2_best') else 'fuzzy-v2 (default)'
    if a.json:
        print(json.dumps(e, indent=1)); return e
    print(f"controller: {e['controller']}")
    print(f"inputs    : own queue {a.queue:g} veh | waiting {a.wait:g} s | opposing queue {a.opp:g} veh")
    for k, v in e['memberships'].items():
        print(f"  {k:<15} " + "  ".join(f"{lab}={m:.2f}" for lab, m in v.items()))
    print("rules fired (strongest first):")
    for r in e['rules_fired']:
        print(f"  {r['rule']}  strength {r['strength']:.3f}  {r['text']}")
    print(f"output strengths: {e['output_strength']}")
    print(f"RECOMMENDED GREEN: {e['green_recommended_s']:.1f} s   (defuzzified {e['green_defuzzified_s']:.2f} s, clamped to the physical 10-60 s)")
    if meta.get('promoted') is False:
        print("note: fuzzy-v2 did NOT clear the promotion rule against v1+GA on the test set (see FINAL_REPORT.md).")
    return e


if __name__ == '__main__':
    main()
