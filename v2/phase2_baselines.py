"""Phase 2: choose the strongest practical baselines on TRAIN only (best fixed duration, actuated gain)."""
import os, sys, json, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import harness as H
from multiprocessing import get_context

def _fixed_row(d):
    return H.evaluate({'type': 'fixed', 'd': int(d)}, 'train')['avg_delay_sec']

def _act_row(g):
    return H.evaluate({'type': 'actuated', 'gain': float(g)}, 'train')['avg_delay_sec']

if __name__ == '__main__':
    t0 = time.time()
    durs = list(range(10, 61))
    gains = [round(x, 2) for x in np.arange(0.5, 4.01, 0.25)]
    with get_context('fork').Pool(10) as pool:
        F = np.array(pool.map(_fixed_row, durs))        # [51, 120]
        A = np.array(pool.map(_act_row, gains))         # [14, 120]
    oracle = F.min(axis=0)                              # best fixed duration for each (scenario, seed): unrealisable reference
    ratio_F = (F / oracle).mean(axis=1)                 # normalised criterion: mean delay relative to the per-run best fixed duration
    raw_F = F.mean(axis=1)
    best_norm = durs[int(ratio_F.argmin())]; best_raw = durs[int(raw_F.argmin())]
    ratio_A = (A / oracle).mean(axis=1); raw_A = A.mean(axis=1)
    best_gain = gains[int(ratio_A.argmin())]; best_gain_raw = gains[int(raw_A.argmin())]
    out = {'criterion': 'mean over TRAIN (scenario,seed) of delay / delay of per-run best fixed duration (oracle denominator)',
           'fixed': {'durations': durs, 'normalized_ratio': ratio_F.tolist(), 'raw_mean_delay': raw_F.tolist(),
                     'best_by_normalized': best_norm, 'best_by_raw_mean': best_raw, 'fixed30_normalized_ratio': float(ratio_F[durs.index(30)]), 'fixed30_raw': float(raw_F[durs.index(30)])},
           'actuated': {'gains': gains, 'normalized_ratio': ratio_A.tolist(), 'raw_mean_delay': raw_A.tolist(), 'best_gain_by_normalized': best_gain, 'best_gain_by_raw': best_gain_raw},
           'oracle_fixed_note': 'per-run oracle (best duration chosen with hindsight on that very run) is an UNREALISABLE lower bound, reported only as a reference',
           'train_best_fixed_delays': F[durs.index(best_norm)].tolist(), 'seconds': time.time() - t0}
    json.dump(out, open(os.path.join(H.HERE, 'data', 'baselines.json'), 'w'), indent=1)
    print(f"{time.time()-t0:.0f}s  best fixed (normalised) = {best_norm}s, best fixed (raw mean) = {best_raw}s, fixed30 ratio={ratio_F[durs.index(30)]:.3f}, best ratio={ratio_F.min():.3f}")
    print(f"actuated best gain (normalised) = {best_gain}, ratio={ratio_A.min():.3f}; (raw) = {best_gain_raw}")
    print('ratio by duration (every 5s):', {d: round(float(ratio_F[durs.index(d)]), 3) for d in range(10, 61, 5)})
