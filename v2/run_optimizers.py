"""Phase 5 runner: 3 structures x 3 optimizers x 3 seeds, budget 2000 evals each, run in parallel (fork pool).
   fuzzy2_bp   : fuzzy-v2, 12 breakpoint genes
   fuzzy2_bpw  : fuzzy-v2, 12 breakpoints + 27 rule weights (39 genes)
   fuzzy1_new  : v1's 3-centre controller RE-TRAINED on the new TRAIN set (isolates 'better data/fitness' from 'better controller')
Fitness = mean over TRAIN (scenario, seed) of avg_delay(controller) / avg_delay(best fixed timer, 29 s)   [lower is better]
Final theta per structure is chosen by VALIDATION performance (never test)."""
import os, sys, json, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import harness as H
import fuzzy2
import optimizers as O
import ga_tune as v1ga           # v1 bounds
from multiprocessing import get_context

BUDGET = 2000
SEEDS = (1, 2, 3)
BEST_FIXED_S = 29                # best fixed duration on TRAIN under the normalised criterion (phase2_baselines.py)
_den = {}

def den(set_name):
    if set_name not in _den:
        _den[set_name] = H.evaluate({'type': 'fixed', 'd': BEST_FIXED_S}, set_name)['avg_delay_sec']
    return _den[set_name]

STRUCT = {
    'fuzzy2_bp':  {'bounds': fuzzy2.bounds(False), 'x0': fuzzy2.DEFAULT_GENES.copy(), 'spec': lambda x: {'type': 'fuzzy2', 'genes': list(map(float, x))}},
    'fuzzy2_bpw': {'bounds': fuzzy2.bounds(True), 'x0': np.concatenate([fuzzy2.DEFAULT_GENES, np.ones(fuzzy2.N_RULES)]), 'spec': lambda x: {'type': 'fuzzy2', 'genes': list(map(float, x))}},
    'fuzzy1_new': {'bounds': v1ga.BOUNDS.copy(), 'x0': np.array([25.0, 60.0, 35.0]), 'spec': lambda x: {'type': 'fuzzy1', 'theta': list(map(float, x))}},
}

def fitness_on(struct, x, set_name):
    d = H.evaluate(STRUCT[struct]['spec'](x), set_name)['avg_delay_sec']
    return float((d / den(set_name)).mean())

def task(args):
    struct, opt, seed = args
    t0 = time.time()
    s = STRUCT[struct]
    x, fbest, hist = O.OPTIMIZERS[opt](lambda x: fitness_on(struct, x, 'train'), s['bounds'], budget=BUDGET, seed=seed, x0=s['x0'])
    if struct.startswith('fuzzy2'):
        x = np.concatenate([fuzzy2.repair(x), x[fuzzy2.N_BP:]])   # store the repaired (valid) genes actually evaluated
    return {'struct': struct, 'opt': opt, 'seed': seed, 'x': [float(v) for v in x], 'train_fitness': fbest,
            'val_fitness': fitness_on(struct, x, 'validation'), 'history': [float(h) for h in hist[::10]] + [float(hist[-1])],
            'evals': len(hist), 'seconds': time.time() - t0}

if __name__ == '__main__':
    out_path = os.path.join(H.HERE, 'data', 'opt_results.json')
    structs = sys.argv[1].split(',') if len(sys.argv) > 1 else list(STRUCT)
    tasks = [(s, o, sd) for s in structs for o in O.OPTIMIZERS for sd in SEEDS]
    results = json.load(open(out_path)) if os.path.exists(out_path) else []
    done = {(r['struct'], r['opt'], r['seed']) for r in results}
    tasks = [t for t in tasks if t not in done]
    print(f"{len(tasks)} tasks, budget {BUDGET} evals each", flush=True)
    t0 = time.time()
    with get_context('fork').Pool(10) as pool:
        for r in pool.imap_unordered(task, tasks):
            results.append(r)
            json.dump(results, open(out_path, 'w'))
            print(f"[{time.time()-t0:5.0f}s] {r['struct']:<11}{r['opt']:<4}seed{r['seed']}  train={r['train_fitness']:.4f}  val={r['val_fitness']:.4f}  ({r['seconds']:.0f}s)", flush=True)
