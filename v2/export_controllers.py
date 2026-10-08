"""Write data/controllers.json: every named controller spec incl. the VALIDATION-selected trained ones (used by predict/server/evaluate)."""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import evaluate_final as E

if __name__ == '__main__':
    specs, info, official = E.all_specs()
    p = os.path.join(E.DATA, 'controllers.json')
    old = json.load(open(p)) if os.path.exists(p) else {}
    out = {'specs': specs, 'official_v2': official, 'selection_info': info, 'promoted': old.get('promoted'),
           'note': 'official_v2 is the validation-best fuzzy-v2 candidate; "promoted" is filled in after the single test evaluation'}
    json.dump(out, open(p, 'w'), indent=1)
    print('official v2 candidate (by validation):', official, info.get(official))
