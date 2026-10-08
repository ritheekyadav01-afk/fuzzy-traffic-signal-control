"""
ga_tune.py
----------
Genetic algorithm that tunes the fuzzy controller's 3 membership centers
theta = (center_queue, center_wait, center_green) to minimize average
vehicle delay, evaluated across several traffic scenarios so the result
generalizes rather than overfitting to one traffic pattern.

Standard GA: tournament selection, blend crossover, gaussian mutation,
elitism. Real-valued encoding (no need to binary-encode for a 3-gene
problem).
"""

import numpy as np
from simulate import run_simulation
from fuzzy_core import green_duration, DEFAULT_THETA

# bounds for each gene: (center_queue, center_wait, center_green)
BOUNDS = np.array([
    [2.0, 48.0],    # center_queue   (domain 0-50)
    [5.0, 115.0],   # center_wait    (domain 0-120)
    [12.0, 58.0],   # center_green   (domain 10-60)
])

# traffic scenarios used to EVALUATE fitness during tuning (training set)
TRAIN_SCENARIOS = {
    'light':    (0.10, 0.10),
    'moderate': (0.20, 0.20),
    'uneven':   (0.35, 0.10),
}
SIM_DURATION = 1800   # 30 simulated minutes per scenario, per fitness eval
SIM_SEEDS = (7, 17, 27)  # fixed seeds -> fair, repeatable comparison between individuals;
                         # averaging several traffic draws keeps the GA from fitting one lucky seed


def fitness(theta):
    """Lower delay = better. Returns NEGATIVE avg delay (so higher fitness = better)."""
    def controller(q, w):
        return green_duration(q, w, theta)

    delays = []
    for r_ns, r_ew in TRAIN_SCENARIOS.values():
        for seed in SIM_SEEDS:
            result = run_simulation(controller, r_ns, r_ew,
                                     duration_seconds=SIM_DURATION, seed=seed)
            delays.append(result['avg_delay_sec'])
    return -float(np.mean(delays))


def random_individual(rng):
    return rng.uniform(BOUNDS[:, 0], BOUNDS[:, 1])


def clip(ind):
    return np.clip(ind, BOUNDS[:, 0], BOUNDS[:, 1])


def tournament_select(pop, fitnesses, rng, k=3):
    idx = rng.integers(0, len(pop), size=k)
    best = idx[np.argmax(fitnesses[idx])]
    return pop[best]


def crossover(p1, p2, rng):
    # blend crossover (BLX-alpha style, alpha=0.3)
    alpha = 0.3
    low = np.minimum(p1, p2) - alpha * np.abs(p1 - p2)
    high = np.maximum(p1, p2) + alpha * np.abs(p1 - p2)
    child = rng.uniform(low, high)
    return clip(child)


def mutate(ind, rng, rate=0.25, sigma_frac=0.1):
    span = BOUNDS[:, 1] - BOUNDS[:, 0]
    mutated = ind.copy()
    for i in range(len(ind)):
        if rng.random() < rate:
            mutated[i] += rng.normal(0, sigma_frac * span[i])
    return clip(mutated)


def run_ga(pop_size=24, generations=30, seed=0, verbose=True):
    rng = np.random.default_rng(seed)
    population = [random_individual(rng) for _ in range(pop_size)]

    # seed one individual with the hand-tuned default, so GA never does worse
    population[0] = np.array(DEFAULT_THETA, dtype=float)

    history = []  # best fitness (as +avg_delay, for readability) per generation
    best_overall = None
    best_overall_fit = -np.inf

    for gen in range(generations):
        fitnesses = np.array([fitness(ind) for ind in population])

        gen_best_idx = np.argmax(fitnesses)
        if fitnesses[gen_best_idx] > best_overall_fit:
            best_overall_fit = fitnesses[gen_best_idx]
            best_overall = population[gen_best_idx].copy()

        history.append(-best_overall_fit)  # store as avg_delay (positive, lower=better)
        if verbose:
            print(f"  gen {gen+1:2d}/{generations}  best avg delay so far: {-best_overall_fit:.3f}s"
                  f"   theta={np.round(best_overall,2)}")

        # elitism: carry the best individual forward unchanged
        new_population = [population[gen_best_idx].copy()]
        while len(new_population) < pop_size:
            p1 = tournament_select(population, fitnesses, rng)
            p2 = tournament_select(population, fitnesses, rng)
            child = crossover(p1, p2, rng)
            child = mutate(child, rng)
            new_population.append(child)
        population = new_population

    return best_overall, history


if __name__ == "__main__":
    print("Running GA to tune fuzzy membership centers...")
    print(f"Training scenarios: {list(TRAIN_SCENARIOS.keys())}, "
          f"{SIM_DURATION}s each per generation\n")
    best_theta, history = run_ga(pop_size=24, generations=30, seed=1)
    print("\nBest theta found:", np.round(best_theta, 3))
    print(f"Default (hand-tuned) theta: {DEFAULT_THETA}")
    print(f"Final best avg delay: {history[-1]:.3f}s")
