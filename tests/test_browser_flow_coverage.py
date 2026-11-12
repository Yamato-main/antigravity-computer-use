"""Preserve the Driver's coverage contract for bounded semantic snapshots."""

import importlib.util
from pathlib import Path
import unittest


MODULE = Path(__file__).parents[1] / 'plugin/scripts/browser_flow.py'
SPEC = importlib.util.spec_from_file_location('browser_flow', MODULE)
flow = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(flow)


class SnapshotCoverageTests(unittest.TestCase):
    def test_partial_ranked_snapshot_keeps_coverage_when_cache_has_no_matches(self):
        omitted = {'budget': 42, 'offscreen': 9, 'unprovable_frame': 2}
        data = {'url': 'https://example.test/catalog', 'snapshot': {
            'outline': '- link "Catalog"', 'action_refs': [], 'content_refs': [],
            'complete': False, 'omitted': omitted, 'continuation': 'opaque-next-page',
        }}
        view, _ = flow._excerpt(data, {'terms': ['target discussion']})
        self.assertEqual(view['matches'], 0)
        self.assertEqual(view['rows'], [])
        self.assertIs(view['complete'], False)
        self.assertEqual(view['omitted'], omitted)
        self.assertEqual(view['continuation'], 'opaque-next-page')
        self.assertEqual(view['matches_scope'], 'returned_snapshot')

    def test_complete_and_unknown_coverage_are_not_confused(self):
        complete, _ = flow._excerpt({'outline': 'ready', 'complete': True, 'omitted': {}}, {})
        self.assertIs(complete['complete'], True)
        self.assertEqual(complete['omitted'], {})
        unknown, _ = flow._excerpt({'outline': 'legacy shape'}, {})
        self.assertIsNone(unknown['complete'])
        self.assertIsNone(unknown['omitted'])


if __name__ == '__main__':
    unittest.main()
