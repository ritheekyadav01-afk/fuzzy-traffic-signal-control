"""Phase 5 analysis: convergence speed and quality of GA / PSO / SA on each structure (TRAIN fitness, VALIDATION score)."""
import os, sys, json
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
res = json.load(open(os.path.join(HERE, 'data', 'opt_results.json')))
rows, md = [], []
md.append("| structure | optimizer | train fitness (mean ± sd over 3 seeds) | best train | validation (mean) | best validation | evals to reach 95% of final improvement | wall s/run |")
md.append("|---|---|---|---|---|---|---|---|")
for struct in sorted({r['struct'] for r in res}):
    for opt in ('GA', 'PSO', 'SA'):
        rs = [r for r in res if r['struct'] == struct and r['opt'] == opt]
        if not rs:
            continue
        tr = np.array([r['train_fitness'] for r in rs]); va = np.array([r['val_fitness'] for r in rs])
        evals95 = []
        for r in rs:
            h = np.array(r['history'][:-1]); start, end = h[0], r['history'][-1]
            thr = start - 0.95 * (start - end)
            evals95.append(int(np.argmax(h <= thr) * 10) if end < start else 0)
        rows.append({'struct': struct, 'opt': opt, 'n': len(rs), 'train_mean': float(tr.mean()), 'train_sd': float(tr.std()), 'train_best': float(tr.min()),
                     'val_mean': float(va.mean()), 'val_best': float(va.min()), 'evals95_mean': float(np.mean(evals95)), 'sec': float(np.mean([r['seconds'] for r in rs]))})
        r0 = rows[-1]
        md.append(f"| {struct} | {opt} | {r0['train_mean']:.4f} ± {r0['train_sd']:.4f} | {r0['train_best']:.4f} | {r0['val_mean']:.4f} | {r0['val_best']:.4f} | {r0['evals95_mean']:.0f} | {r0['sec']:.0f} |")
json.dump(rows, open(os.path.join(HERE, 'data', 'optimizer_summary.json'), 'w'), indent=1)
open(os.path.join(HERE, 'data', 'optimizer_table.md'), 'w').write("\n".join(md) + "\n")
print("\n".join(md))
