"""Deterministic regression tests for toy network."""
import unittest
from brain_gap_lab import EDGES, STRONG, WEAK, comparison, simulate


class BrainGapTests(unittest.TestCase):
    def test_structure(self):
        self.assertEqual(set(STRONG), set(WEAK))
        self.assertEqual(set(STRONG), set(EDGES))
        self.assertTrue(all(STRONG[k] > 0 and WEAK[k] > 0 for k in EDGES))

    def test_distinct_dynamics(self):
        result = comparison()
        self.assertTrue(result["same_topology"])
        self.assertTrue(result["same_signs"])
        self.assertGreater(result["strong_last"], 0.5)
        self.assertLess(result["weak_last"], 0.05)
        self.assertGreater(result["difference"], 0.5)

    def test_repeatable(self):
        self.assertEqual(simulate(STRONG), simulate(STRONG))

    def test_steps(self):
        self.assertEqual(len(simulate(STRONG, steps=3).motor), 3)

    def test_rejects_missing_edge(self):
        with self.assertRaises(ValueError):
            simulate({(0, 1): 1.0})

    def test_rejects_negative_weights(self):
        values = dict(STRONG)
        values[(1, 2)] = -1.0
        with self.assertRaises(ValueError):
            simulate(values)

    def test_rejects_invalid_timing(self):
        for steps, leak in [(0, 0.2), (1, -0.1), (2, 1.0)]:
            with self.assertRaises(ValueError):
                simulate(STRONG, steps=steps, leak=leak)


if __name__ == "__main__":
    unittest.main()
