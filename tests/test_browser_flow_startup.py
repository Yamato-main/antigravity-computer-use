"""Bounded startup observations must tolerate transient extra windows."""

import importlib.util
from pathlib import Path
import unittest


MODULE = Path(__file__).parents[1] / 'plugin/scripts/browser_flow.py'
SPEC = importlib.util.spec_from_file_location('browser_flow', MODULE)
flow = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(flow)


class NoWaitCancellation:
    def __init__(self):
        self.waits = []

    def is_set(self):
        return False

    def wait(self, seconds):
        self.waits.append(seconds)


class BrowserStartupTests(unittest.TestCase):
    def run_open(self, observations, refused_windows=(), refusal_code='browser_wrong_target_refused'):
        calls, cancelled = [], NoWaitCancellation()
        windows = iter(observations)

        def send(name, args, timeout):
            calls.append((name, args))
            if name == 'browser_prepare':
                data = {'prepared_pid': 99}
            elif name == 'list_windows':
                data = {'windows': [
                    {'pid': 99, 'window_id': ident, 'layer': 0} for ident in next(windows)
                ]}
            elif name == 'get_browser_state':
                if args['window_id'] in refused_windows:
                    return {'isError': True, 'structuredContent': {
                        'refusal': {'code': refusal_code}, 'status': 'refused',
                    }}
                data = {'binding_quality': 'exact', 'target_id': 'target',
                        'tabs': [{'tab_id': 'tab', 'active': True}]}
            else:
                data = {}
            return {'structuredContent': data, 'content': []}

        result = flow.BrowserFlows().run(
            {'session': 'startup', 'steps': [{'op': 'open'}, {'op': 'end'}]},
            send, cancelled,
        )
        return result, calls, cancelled.waits

    def test_waits_for_a_unique_window_after_empty_or_transient_extra_windows(self):
        for initial in ([], [11, 12, 13]):
            with self.subTest(initial=initial):
                result, calls, waits = self.run_open([initial, [12]])
                self.assertFalse(result['isError'], result)
                self.assertEqual(waits, [0.35])
                bindings = [args for name, args in calls if name == 'get_browser_state']
                self.assertEqual(bindings, [{'session': 'startup', 'pid': 99, 'window_id': 12}])
                self.assertEqual(result['structuredContent']['driver_calls'], 5)

    def test_persistent_ambiguity_refuses_after_the_existing_observation_budget(self):
        result, calls, waits = self.run_open([[11, 12]] * 5)
        self.assertTrue(result['isError'])
        self.assertEqual(len(waits), 4)
        self.assertEqual([name for name, _ in calls], ['browser_prepare'] + ['list_windows'] * 5)
        self.assertEqual(result['structuredContent']['failed_step'], 1)
        self.assertEqual(result['structuredContent']['completed'], [])
        self.assertIn('expected one browser window', result['structuredContent']['error'])

    def test_reobserves_after_a_transient_window_fails_exact_binding(self):
        result, calls, waits = self.run_open([[11], [12]], refused_windows={11})
        self.assertFalse(result['isError'], result)
        self.assertEqual(waits, [0.35])
        self.assertEqual([args['window_id'] for name, args in calls if name == 'get_browser_state'], [11, 12])

    def test_never_repeats_an_unchanged_refused_binding(self):
        result, calls, waits = self.run_open([[11]] * 5, refused_windows={11})
        self.assertTrue(result['isError'])
        self.assertEqual(len(waits), 4)
        self.assertEqual([args['window_id'] for name, args in calls if name == 'get_browser_state'], [11])
        self.assertEqual(result['structuredContent']['driver_detail']['refusal']['code'],
                         'browser_wrong_target_refused')

    def test_consent_refusal_stops_immediately(self):
        result, calls, waits = self.run_open([[11]], refused_windows={11},
                                             refusal_code='browser_consent_required')
        self.assertTrue(result['isError'])
        self.assertEqual(waits, [])
        self.assertEqual([name for name, _ in calls], ['browser_prepare', 'list_windows', 'get_browser_state'])


if __name__ == '__main__':
    unittest.main()
