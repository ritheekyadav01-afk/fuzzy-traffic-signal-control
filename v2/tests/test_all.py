"""Unit tests.  Run:  /usr/bin/python3 -m unittest discover -s v2/tests -v     (from the project root)
None of these tests reads the TEST scenario set's results."""
import os, sys, json, unittest
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); V2 = os.path.dirname(HERE); ROOT = os.path.dirname(V2)
sys.path.insert(0, V2); sys.path.insert(0, ROOT)
import fuzzy_core as v1f
from simulate import run_simulation as run_v1, fixed_timer_controller as fixed_v1
import scenarios as S
import simulate2 as sim2
import controllers as C
import fuzzy2
import predict as P

V1_OFFICIAL = [32.784, 30.785, 52.154]


class TestMemberships(unittest.TestCase):
    def test_v1_partition_sums_to_one(self):
        rng = np.random.default_rng(0)
        for _ in range(300):
            c = rng.uniform(2, 48); x = rng.uniform(0, 50)
            self.assertAlmostEqual(sum(v1f._memberships(x, 0, 50, c)), 1.0, places=9)

    def test_v2_partition_valid_for_random_breakpoints(self):
        rng = np.random.default_rng(1)
        for _ in range(300):
            g = fuzzy2.repair(rng.uniform(0, 120, size=12))
            for v, (lo, hi) in enumerate(fuzzy2.DOMS):
                a, b, c = g[3 * v:3 * v + 3]
                self.assertTrue(lo < a < b < c < hi, (v, a, b, c))
            f = fuzzy2.Fuzzy2(g)
            for _ in range(20):
                q, w, o = rng.uniform(0, 60), rng.uniform(0, 120), rng.uniform(0, 60)
                for m in f.memberships(q, w, o):
                    self.assertAlmostEqual(sum(m), 1.0, places=9)
                    self.assertTrue(all(0 <= v <= 1 for v in m))

    def test_repair_is_idempotent(self):
        g = fuzzy2.repair(np.random.default_rng(2).uniform(0, 120, 12))
        self.assertTrue(np.allclose(g, fuzzy2.repair(g)))

    def test_rulebase_complete(self):
        self.assertEqual(len(fuzzy2.RULES2), 27)
        self.assertEqual(len({(q, w, o) for q, w, o, _ in fuzzy2.RULES2}), 27)


class TestMonotonicity(unittest.TestCase):
    def _violations(self, f, tol=1.0):
        # tolerance 1 s (~2% of the 50 s output range): centroid defuzzification blends adjacent output sets, which can
        # produce sub-second non-monotone wiggles even when the RULE base is monotone (measured max for the default: 0.93 s).
        up = down = 0
        for w in (5, 30, 60, 100):
            for o in (0, 10, 30, 60):
                prev = -1
                for q in range(0, 61):
                    g = min(60, max(10, f(q, w, o)))
                    up += g < prev - tol; prev = g
            for q in (0, 10, 30, 60):
                prev = 1e9
                for o in range(0, 61):
                    g = min(60, max(10, f(q, w, o)))
                    down += g > prev + tol; prev = g
        return up, down

    def test_default_monotone(self):
        up, down = self._violations(fuzzy2.Fuzzy2())
        self.assertEqual((up, down), (0, 0))

    def test_trained_report_only(self):
        """Trained controllers may legitimately trade monotonicity for delay; we only record the count."""
        p = os.path.join(V2, 'data', 'controllers.json')
        if not os.path.exists(p):
            self.skipTest('no trained controllers yet')
        with open(p) as fh:
            specs = json.load(fh)['specs']
        for name, s in specs.items():
            if s['type'] == 'fuzzy2':
                up, down = self._violations(fuzzy2.Fuzzy2(np.asarray(s['genes'], float)))
                print(f"\n  [monotonicity] {name}: own-queue violations={up}, opposing-queue violations={down} (of 1024 checks each)")


class TestSimulator(unittest.TestCase):
    def _check_conservation(self, ctrl, scn, seed):
        r = sim2.run_simulation2(ctrl, scn, seed=seed)
        self.assertAlmostEqual(r['arrived_ns'], r['served_ns'] + r['final_queue_ns'], places=6)
        self.assertAlmostEqual(r['arrived_ew'], r['served_ew'] + r['final_queue_ew'], places=6)
        self.assertEqual(r['total_vehicles'], r['arrived_ns'] + r['arrived_ew'])
        self.assertLessEqual(r['served_total'], r['total_vehicles'] + 1e-9)

    def test_conservation_all_profiles(self):
        sets = S.load()
        for s in sets['train'][:7] + sets['legacy']:
            for c in (C.fixed(30), C.actuated(3.0), C.pressure_split(), C.Fuzzy2() if hasattr(C, 'Fuzzy2') else fuzzy2.Fuzzy2()):
                self._check_conservation(c, s, 5)

    def test_service_never_exceeds_saturation(self):
        s = S.load()['legacy'][4]
        r = sim2.run_simulation2(C.fixed(30), s, seed=1)
        self.assertLessEqual(r['served_total'], 0.5 * 3600 + 1e-6)

    def test_reproduces_v1_exactly(self):
        for scn in S.legacy_scenarios():
            a, b = scn['knots'][0][1:]
            for seed in (99, 7):
                for name, c in {'fixed': fixed_v1, 'fz': lambda q, w: v1f.green_duration(q, w, V1_OFFICIAL)}.items():
                    r1 = run_v1(c, a, b, duration_seconds=3600, seed=seed); r2 = sim2.run_simulation2(c, scn, seed=seed)
                    self.assertLess(abs(r1['avg_delay_sec'] - r2['avg_delay_sec']) / r1['avg_delay_sec'], 0.005)   # brief: within 0.5%
                    self.assertEqual(r1['avg_delay_sec'], r2['avg_delay_sec'])                                 # in fact bit-identical
                    self.assertEqual(r1['total_vehicles'], r2['total_vehicles'])

    def test_published_v1_numbers(self):
        scn = S.legacy_scenarios()[2]       # uneven, seed 99
        f = sim2.run_simulation2(fixed_v1, scn, seed=99)['avg_delay_sec']
        g = sim2.run_simulation2(C.fuzzy_v1(V1_OFFICIAL), scn, seed=99)['avg_delay_sec']
        self.assertAlmostEqual(f, 506.3, delta=0.05); self.assertAlmostEqual(g, 217.7, delta=0.05)

    def test_fast_v1_equals_v1(self):
        rng = np.random.default_rng(3)
        fast = C.fuzzy_v1(V1_OFFICIAL)
        for _ in range(200):
            q, w = rng.uniform(0, 60), rng.uniform(0, 130)
            self.assertAlmostEqual(fast(q, w), v1f.green_duration(q, w, V1_OFFICIAL), places=9)

    def test_determinism(self):
        s = S.load()['train'][3]
        a = sim2.run_simulation2(C.actuated(3.0), s, seed=11); b = sim2.run_simulation2(C.actuated(3.0), s, seed=11)
        c = sim2.run_simulation2(C.actuated(3.0), s, seed=12)
        self.assertEqual(a, b); self.assertNotEqual(a['avg_delay_sec'], c['avg_delay_sec'])

    def test_arrivals_independent_of_controller(self):
        s = S.load()['train'][0]
        r1 = sim2.run_simulation2(C.fixed(15), s, seed=3); r2 = sim2.run_simulation2(C.fixed(60), s, seed=3)
        self.assertEqual(r1['total_vehicles'], r2['total_vehicles'])

    def test_opposing_arg_detection(self):
        self.assertFalse(sim2.wants_opposing(fixed_v1))          # 3 params but the 3rd has a default
        self.assertFalse(sim2.wants_opposing(lambda q, w: 30))
        self.assertTrue(sim2.wants_opposing(lambda q, w, o: 30))
        self.assertTrue(sim2.wants_opposing(C.pressure_split()))

    def test_trace_hook_matches_result(self):
        s = S.load()['legacy'][2]; tr = []
        r = sim2.run_simulation2(C.fixed(30), s, seed=99, trace=tr)
        self.assertEqual(len(tr), 3600)
        self.assertAlmostEqual(tr[-1]['cumulative_delay'] / r['total_vehicles'], r['avg_delay_sec'], places=1)
        self.assertAlmostEqual(tr[-1]['departed_ns'] + tr[-1]['departed_ew'], r['served_total'], places=1)
        ticks = []
        sim2.run_simulation2(C.fixed(30), s, seed=99, on_tick=lambda *a: ticks.append(a))
        self.assertEqual(len(ticks), 3600)


class TestScenarios(unittest.TestCase):
    def test_sizes_and_disjoint(self):
        sets = S.load()
        self.assertEqual([len(sets[k]) for k in ('train', 'validation', 'test', 'legacy')], [40, 20, 60, 5])
        sig = lambda s: tuple(round(v, 6) for k in s['knots'] for v in k)
        seen = set()
        for k in ('train', 'validation', 'test'):
            for s in sets[k]:
                self.assertNotIn(sig(s), seen); seen.add(sig(s))
        self.assertFalse(set(sum((s['seeds'] for s in sets['test']), [])) & set(sum((s['seeds'] for s in sets['train'] + sets['validation']), [])))

    def test_rates_in_range_and_reproducible(self):
        sets = S.load()
        for k in ('train', 'validation', 'test'):
            for s in sets[k]:
                a, b = S.rate_arrays(s)
                self.assertTrue(a.min() >= S.RATE_MIN - 1e-9 and a.max() <= S.RATE_MAX + 1e-9 and b.min() >= S.RATE_MIN - 1e-9 and b.max() <= S.RATE_MAX + 1e-9)
        regenerated = S.build_all()['sets']
        self.assertEqual(json.loads(json.dumps(regenerated)), sets)     # fixed seeds -> identical files


class TestControllers(unittest.TestCase):
    def test_outputs_within_physical_range_after_clamp(self):
        rng = np.random.default_rng(4)
        ctrls = [C.fixed(30), C.actuated(3), C.pressure_split(), C.longest_queue_first(), C.fuzzy_v1(V1_OFFICIAL), C.build({'type': 'fuzzy2', 'genes': list(fuzzy2.DEFAULT_GENES)})]
        for c in ctrls:
            for _ in range(100):
                q, w, o = rng.uniform(0, 500), rng.uniform(0, 500), rng.uniform(0, 500)
                g = c(q, w, o) if sim2.wants_opposing(c) else c(q, w)
                self.assertTrue(np.isfinite(g))

    def test_explainability(self):
        f = fuzzy2.Fuzzy2(); e = P.explain(f, 30, 60, 8)
        self.assertGreaterEqual(e['n_rules_fired'], 1)
        self.assertAlmostEqual(e['green_defuzzified_s'], f(30, 60, 8), places=1)
        self.assertTrue(10 <= e['green_recommended_s'] <= 60)

    def test_weights_gene_vector_accepted(self):
        g = np.concatenate([fuzzy2.DEFAULT_GENES, np.full(27, 0.7)])
        self.assertTrue(10 <= min(60, max(10, fuzzy2.Fuzzy2(g)(20, 40, 10))) <= 60)


class TestServer(unittest.TestCase):
    def test_simulate_request_matches_direct_run(self):
        import server
        p = server.parse_params({'preset': 'uneven', 'seed': '99', 'controller': 'actuated'})
        _, out, summary = server.simulate_request(p)
        direct = sim2.run_simulation2(C.actuated(3.0 if 'actuated' not in server._SPECS else server._SPECS['actuated']['gain']), S.legacy_scenarios()[2], seed=99)
        self.assertEqual(out['fuzzy_ga']['result']['avg_delay_sec'], direct['avg_delay_sec'])
        self.assertAlmostEqual(summary['fixed_30s_avg_delay_s'], 506.3, delta=0.05)

    def test_bad_input_rejected(self):
        import server
        with self.assertRaises(ValueError):
            server.parse_params({'controller': 'nope'})
        with self.assertRaises(ValueError):
            server.parse_params({'profile': 'nope'})


if __name__ == '__main__':
    unittest.main()
