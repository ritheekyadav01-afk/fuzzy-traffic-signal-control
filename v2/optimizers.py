"""
Phase 5 - three optimizers with an IDENTICAL interface and an IDENTICAL evaluation budget.
All minimise f(x) over a box `bounds` (n x 2).  Each returns (best_x, best_f, history) where history[i] is the
best-so-far value after i+1 fitness evaluations (so convergence curves are comparable across algorithms).
`x0` (optional) is a known-good starting candidate (the hand-designed default) injected into every algorithm
(GA: individual 0, PSO: particle 0, SA: starting state) so no optimizer is advantaged by it.
"""
import numpy as np


class Counter:
    """Wraps f, enforces the budget and records best-so-far history."""
    def __init__(self, f, budget):
        self.f, self.budget, self.n = f, budget, 0
        self.best_x, self.best_f, self.history = None, np.inf, []

    @property
    def left(self):
        return self.budget - self.n

    def __call__(self, x):
        v = float(self.f(x))
        self.n += 1
        if v < self.best_f:
            self.best_f, self.best_x = v, np.array(x, dtype=float).copy()
        self.history.append(self.best_f)
        return v


def _clip(x, b):
    return np.clip(x, b[:, 0], b[:, 1])


def ga(f, bounds, budget=2000, seed=0, x0=None, pop_size=40, tournament=3, cx_alpha=0.3, sigma_frac=0.1):
    """Real-coded GA: tournament selection, BLX-alpha crossover, gaussian mutation, 1-elitism (same operators as v1's ga_tune)."""
    rng = np.random.default_rng(seed)
    b = np.asarray(bounds, float); n = len(b); span = b[:, 1] - b[:, 0]
    rate = max(0.25, 2.0 / n)
    cf = Counter(f, budget)
    pop = [rng.uniform(b[:, 0], b[:, 1]) for _ in range(pop_size)]
    if x0 is not None:
        pop[0] = _clip(np.asarray(x0, float), b)
    fit = np.array([cf(x) for x in pop])
    while cf.left > 0:
        elite = int(fit.argmin())
        new_pop, new_fit = [pop[elite].copy()], [fit[elite]]
        while len(new_pop) < pop_size and cf.left > 0:
            def pick():
                idx = rng.integers(0, len(pop), size=tournament)
                return pop[idx[np.argmin(fit[idx])]]
            p1, p2 = pick(), pick()
            lo = np.minimum(p1, p2) - cx_alpha * np.abs(p1 - p2); hi = np.maximum(p1, p2) + cx_alpha * np.abs(p1 - p2)
            child = rng.uniform(lo, hi)
            m = rng.random(n) < rate
            child = child + m * rng.normal(0, sigma_frac * span)
            child = _clip(child, b)
            new_pop.append(child); new_fit.append(cf(child))
        pop, fit = new_pop, np.array(new_fit)
    return cf.best_x, cf.best_f, cf.history


def pso(f, bounds, budget=2000, seed=0, x0=None, swarm=40, w=0.7298, c1=1.49618, c2=1.49618, vmax_frac=0.25):
    """Global-best PSO with constriction-style coefficients and velocity clamping."""
    rng = np.random.default_rng(seed)
    b = np.asarray(bounds, float); n = len(b); span = b[:, 1] - b[:, 0]
    cf = Counter(f, budget)
    X = rng.uniform(b[:, 0], b[:, 1], size=(swarm, n))
    if x0 is not None:
        X[0] = _clip(np.asarray(x0, float), b)
    V = rng.uniform(-0.1, 0.1, size=(swarm, n)) * span
    F = np.array([cf(x) for x in X])
    P, PF = X.copy(), F.copy()
    g = int(PF.argmin()); G, GF = P[g].copy(), PF[g]
    while cf.left > 0:
        for i in range(swarm):
            if cf.left <= 0:
                break
            r1, r2 = rng.random(n), rng.random(n)
            V[i] = w * V[i] + c1 * r1 * (P[i] - X[i]) + c2 * r2 * (G - X[i])
            V[i] = np.clip(V[i], -vmax_frac * span, vmax_frac * span)
            X[i] = X[i] + V[i]
            lo, hi = X[i] < b[:, 0], X[i] > b[:, 1]          # reflect-and-damp at the walls
            X[i] = _clip(X[i], b); V[i][lo | hi] *= -0.5
            fv = cf(X[i])
            if fv < PF[i]:
                PF[i], P[i] = fv, X[i].copy()
                if fv < GF:
                    GF, G = fv, X[i].copy()
    return cf.best_x, cf.best_f, cf.history


def sa(f, bounds, budget=2000, seed=0, x0=None, t0=0.05, t1=0.0005, step0=0.15, step1=0.01):
    """Simulated annealing: gaussian neighbour (step shrinks geometrically), Metropolis acceptance, geometric cooling.
    Temperatures are in units of the fitness (relative delay ratio, ~0.4-1.5)."""
    rng = np.random.default_rng(seed)
    b = np.asarray(bounds, float); n = len(b); span = b[:, 1] - b[:, 0]
    cf = Counter(f, budget)
    x = _clip(np.asarray(x0, float), b) if x0 is not None else rng.uniform(b[:, 0], b[:, 1])
    fx = cf(x)
    steps = budget - 1
    for k in range(steps):
        frac = k / max(1, steps - 1)
        T = t0 * (t1 / t0) ** frac
        sig = step0 * (step1 / step0) ** frac
        cand = x.copy()
        m = rng.random(n) < max(0.34, 2.0 / n)
        if not m.any():
            m[rng.integers(0, n)] = True
        cand[m] += rng.normal(0, sig * span[m])
        cand = _clip(cand, b)
        fc = cf(cand)
        if fc <= fx or rng.random() < np.exp(-(fc - fx) / T):
            x, fx = cand, fc
    return cf.best_x, cf.best_f, cf.history


OPTIMIZERS = {'GA': ga, 'PSO': pso, 'SA': sa}
