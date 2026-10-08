"""
Phase 4 - fuzzy-v2: a 3-input Mamdani controller that also sees the OPPOSING queue.

Inputs   own_queue Q in [0,60]   waiting W in [0,120] s   opposing_queue O in [0,60]
Output   green G, universe [0,80] s (clamped by the simulator to the physical 10-60 s); terms short/medium/long

Each variable is a 3-term Ruspini partition defined by 3 breakpoints a<b<c:
    low  = trapezoid(lo, lo, a, b)   (1 up to a, falls to 0 at b)
    med  = triangle(a, b, c)
    high = trapezoid(b, c, hi, hi)   (0 up to b, rises to 1 at c)
=> memberships always sum to 1 (valid partition) for ANY a<b<c.  v1 is the special case a=lo, c=hi.

Gene encoding (12 real genes, in real units, + optional 27 rule weights):
    genes[0:3]   Q breakpoints (a,b,c)        genes[3:6]  W breakpoints
    genes[6:9]   O breakpoints                genes[9:12] G (output) breakpoints
    genes[12:39] (optional) rule weights in [WEIGHT_MIN, 1], rule order = RULES2 order
`repair()` sorts each triple and enforces a minimum gap, so every gene vector decodes to a valid partition.
Inference: min for AND, rule weight scales the firing strength, max aggregation, centroid defuzzification (81-pt universe).
"""
import numpy as np

Q_DOM = (0.0, 60.0)
W_DOM = (0.0, 120.0)
O_DOM = (0.0, 60.0)
G_DOM = (0.0, 80.0)      # output universe is wider than the physical [10,60]: the simulator clamps, and a wide universe lets the centroid reach the ends
DOMS = [Q_DOM, W_DOM, O_DOM, G_DOM]
MIN_GAP_FRAC = 0.02          # breakpoints at least 2% of the domain apart
WEIGHT_MIN = 0.2
N_BP = 12
N_RULES = 27
U = np.arange(G_DOM[0], G_DOM[1] + 1.0, 1.0)

Q_LABELS = ('low', 'med', 'high')
W_LABELS = ('short', 'moderate', 'long')
O_LABELS = ('low', 'med', 'high')
G_LABELS = ('short', 'medium', 'long')


def _build_rules():
    """27 rules, one per (own queue, wait, opposing queue).  Consequent logic (documented in rules.txt):
       base level = own-queue level (low 0, med 1, high 2)
       +1 if the direction has waited long and has real demand (own >= med)         -> starving approach clears
       -1 if the opposing queue is high and own queue is not high                   -> yield to the heavier side
       -1 if wait is short, own is med and opposing is not low                      -> it just had green; share
       clipped to [0,2].  (own high keeps 'long' even if opposing is high: when both are saturated, long greens
       waste the least time in clearance.)"""
    rules = []
    for qi, ql in enumerate(Q_LABELS):
        for wi, wl in enumerate(W_LABELS):
            for oi, ol in enumerate(O_LABELS):
                g = qi
                if wi == 2 and qi >= 1:
                    g += 1
                if oi == 2 and qi < 2:
                    g -= 1
                if wi == 0 and qi == 1 and oi >= 1:
                    g -= 1
                g = max(0, min(2, g))
                rules.append((ql, wl, ol, G_LABELS[g]))
    return rules


RULES2 = _build_rules()
RULE_IDX = [(Q_LABELS.index(q), W_LABELS.index(w), O_LABELS.index(o), G_LABELS.index(g)) for q, w, o, g in RULES2]

# hand-designed default breakpoints (a,b,c) per variable, in real units
DEFAULT_GENES = np.array([6.0, 25.0, 50.0,      # Q
                          12.0, 55.0, 100.0,    # W
                          6.0, 25.0, 50.0,      # O
                          15.0, 35.0, 55.0])    # G


def repair(genes):
    """Return a valid 12-vector: each triple sorted, inside its domain, min gaps enforced."""
    g = np.asarray(genes, dtype=float)[:N_BP].copy()
    for v, (lo, hi) in enumerate(DOMS):
        gap = MIN_GAP_FRAC * (hi - lo)
        t = np.sort(np.clip(g[3 * v:3 * v + 3], lo + gap, hi - gap))
        t[1] = max(t[1], t[0] + gap)
        t[2] = max(t[2], t[1] + gap)
        if t[2] > hi - gap / 2:                 # pushed past the top: shift the triple down
            shift = t[2] - (hi - gap / 2)
            t -= shift
            t[0] = max(t[0], lo + gap / 2)
        g[3 * v:3 * v + 3] = t
    return g


def bounds(with_weights=False):
    b = []
    for lo, hi in DOMS:
        gap = MIN_GAP_FRAC * (hi - lo)
        b += [(lo + gap, hi - gap)] * 3
    if with_weights:
        b += [(WEIGHT_MIN, 1.0)] * N_RULES
    return np.array(b, dtype=float)


def _part(x, a, b, c, lo, hi):
    """(low, med, high) memberships of x for breakpoints a<b<c in [lo,hi]."""
    if x <= a:
        return 1.0, 0.0, 0.0
    if x >= c:
        return 0.0, 0.0, 1.0
    if x < b:
        m = (x - a) / (b - a)
        return 1.0 - m, m, 0.0
    m = (c - x) / (c - b)
    return 0.0, m, 1.0 - m


def _out_shapes(a, b, c):
    lo, hi = G_DOM
    u = U
    short = np.where(u <= a, 1.0, np.where(u >= b, 0.0, (b - u) / (b - a)))
    med = np.clip(np.minimum((u - a) / (b - a), (c - u) / (c - b)), 0.0, 1.0)
    long_ = np.where(u >= c, 1.0, np.where(u <= b, 0.0, (u - b) / (c - b)))
    return short, med, long_


class Fuzzy2:
    wants_opposing = True

    def __init__(self, genes=None, weights=None):
        g = np.asarray(DEFAULT_GENES if genes is None else genes, dtype=float)
        if weights is None and len(g) >= N_BP + N_RULES:
            weights = g[N_BP:N_BP + N_RULES]
        self.bp = repair(g)
        self.w = np.ones(N_RULES) if weights is None else np.clip(np.asarray(weights, float), WEIGHT_MIN, 1.0)
        self._shapes = _out_shapes(*self.bp[9:12])
        self._pq = tuple(self.bp[0:3]); self._pw = tuple(self.bp[3:6]); self._po = tuple(self.bp[6:9])

    def memberships(self, q, w, o):
        q = min(max(q, Q_DOM[0]), Q_DOM[1]); w = min(max(w, W_DOM[0]), W_DOM[1]); o = min(max(o, O_DOM[0]), O_DOM[1])
        return (_part(q, *self._pq, *Q_DOM), _part(w, *self._pw, *W_DOM), _part(o, *self._po, *O_DOM))

    def fire(self, q, w, o):
        """Per-rule firing strengths (weighted) and per-output-label aggregated strengths."""
        mq, mw, mo = self.memberships(q, w, o)
        strengths = [min(mq[i], mw[j], mo[k]) * self.w[r] for r, (i, j, k, _) in enumerate(RULE_IDX)]
        out = [0.0, 0.0, 0.0]
        for r, (_, _, _, gl) in enumerate(RULE_IDX):
            if strengths[r] > out[gl]:
                out[gl] = strengths[r]
        return strengths, out

    def __call__(self, queue, waiting_time, opposing_queue):
        _, out = self.fire(queue, waiting_time, opposing_queue)
        s0, s1, s2 = out
        sh = self._shapes
        agg = np.maximum(np.maximum(np.minimum(sh[0], s0), np.minimum(sh[1], s1)), np.minimum(sh[2], s2))
        tot = agg.sum()
        if tot <= 0.0:
            return float(U.mean())
        return float((U * agg).sum() / tot)


def rules_text():
    lines = ["FUZZY-V2 RULE BASE (27 rules, IF own_queue AND waiting AND opposing_queue THEN green)", ""]
    for r, (ql, wl, ol, gl) in enumerate(RULES2, 1):
        lines.append(f"R{r:02d}: IF own_queue is {ql:<4} AND waiting is {wl:<8} AND opposing_queue is {ol:<4} THEN green is {gl}")
    lines += ["", "Rule construction (so the table is explainable, not arbitrary):",
              "  base level = own-queue level (low->short, med->medium, high->long)",
              "  +1 level  if waiting is 'long' and own queue >= med   (a starved approach with demand clears)",
              "  -1 level  if opposing queue is 'high' and own queue is not high   (yield to the heavier side)",
              "  -1 level  if waiting is 'short', own is 'med' and opposing is not 'low'   (it just had green; share the cycle)",
              "  levels clipped to [short..long].  When BOTH queues are high the rule is 'long': in saturation long greens",
              "  waste the least time on the 3 s clearance interval.", "",
              "Inference: min (AND), optional per-rule weight multiplies firing strength, max aggregation, centroid defuzzification.",
              "Gene encoding: 12 breakpoints (a<b<c for own_queue, waiting, opposing_queue, green) + optional 27 rule weights in [0.2,1].",
              "Default breakpoints (own, wait, opp, green):  " + ", ".join(f"({DEFAULT_GENES[i]:g},{DEFAULT_GENES[i+1]:g},{DEFAULT_GENES[i+2]:g})" for i in range(0, 12, 3))]
    return "\n".join(lines) + "\n"


if __name__ == '__main__':
    import os
    open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'rules.txt'), 'w').write(rules_text())
    print(rules_text())
