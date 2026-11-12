"""Verify batched readiness and screenshots without sleeping or launching a browser."""

import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch


MODULE = Path(__file__).parents[1] / 'plugin/scripts/browser_flow.py'
SPEC = importlib.util.spec_from_file_location('browser_flow', MODULE)
flow = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(flow)


class Clock:
    def __init__(self):
        self.now = 0
        self.cancelled = False

    def is_set(self):
        return self.cancelled

    def wait(self, seconds):
        self.now += seconds
        return self.cancelled


class ReadinessTests(unittest.TestCase):
    def setUp(self):
        self.clock = Clock()
        self.calls = []

    def run_flow(self, steps, observations):
        snapshots = iter(observations)

        def send(name, args, timeout):
            self.calls.append((name, args, timeout))
            if 'pid' in args:
                data = {'binding_quality': 'exact', 'target_id': 'target', 'tabs': [{'tab_id': 'tab'}]}
            elif name == 'get_browser_state':
                data = next(snapshots)
            else:
                data = {}
            media = [{'type': 'image', 'data': data['outline'], 'mimeType': 'image/png'}] if args.get('include_screenshot') else []
            return {'structuredContent': data, 'content': media}

        with patch.object(flow.time, 'monotonic', lambda: self.clock.now):
            return flow.BrowserFlows().run({'session': 'test', 'steps': [
                {'op': 'bind', 'pid': 1, 'window_id': 2}, *steps,
            ]}, send, self.clock)

    def test_waits_for_each_image_and_returns_them_in_order(self):
        def capture(text):
            return {'op': 'read', 'expect_text': text, 'wait_ms': 1000, 'screenshot': True}

        result = self.run_flow([
            capture('First expanded'), {'op': 'click', 'role': 'link'}, capture('Second expanded'), {'op': 'end'},
        ], [
            {'outline': 'Loading'}, {'outline': 'First expanded'},
            {'outline': 'First expanded', 'complete': True,
             'refs': [{'ref': 'p3:0', 'role': 'link', 'actions': ['click']}]},
            {'outline': 'Loading'}, {'outline': 'Second expanded'}, {'outline': 'Second expanded'},
        ])

        self.assertFalse(result['isError'], result)
        reads = [step for step in result['structuredContent']['completed'] if step['op'] == 'read']
        self.assertEqual([step['observations'] for step in reads], [2, 2])
        self.assertEqual([step['media_offset'] for step in reads], [0, 1])
        self.assertEqual([block['data'] for block in result['content'][1:]], ['First expanded', 'Second expanded'])
        self.assertEqual([args['ref'] for name, args, _ in self.calls if name == 'browser_click'], ['p3:0'])
        self.assertEqual([args['include_screenshot'] for name, args, _ in self.calls
                          if name == 'get_browser_state' and 'pid' not in args],
                         [False, False, True, False, False, True])

    def test_timeout_leaves_the_latest_observation_and_stops(self):
        result = self.run_flow([
            {'op': 'navigate', 'url': 'https://example.test/'},
            {'op': 'read', 'expect_text': 'Ready', 'wait_ms': 500, 'screenshot': True},
            {'op': 'end'},
        ], [{'outline': 'Loading'}, {'outline': 'Still loading', 'snapshot': {'id': 'p2'}}])

        data = result['structuredContent']
        self.assertTrue(result['isError'])
        self.assertIn('Readiness condition was not met', data['error'])
        self.assertEqual(data['driver_detail']['snapshot_id'], 'p2')
        self.assertEqual([name for name, _, _ in self.calls], [
            'get_browser_state', 'browser_navigate', 'get_browser_state', 'get_browser_state',
        ])
        self.assertEqual([timeout for _, _, timeout in self.calls[-2:]], [0.5, 0.25])

    def test_does_not_capture_when_scope_cannot_be_reused(self):
        result = self.run_flow([
            {'op': 'read', 'expect_text': 'Ready', 'wait_ms': 500, 'scope_ref': 'p1:0'},
        ], [])
        self.assertTrue(result['isError'])
        self.assertEqual(self.calls, [])

    def test_role_click_refuses_ambiguous_links(self):
        result = self.run_flow([{'op': 'read'}, {'op': 'click', 'role': 'link'}], [
            {'complete': True, 'refs': [{'ref': ref, 'role': 'link', 'actions': ['click']} for ref in ('p1:0', 'p1:1')]},
        ])
        self.assertTrue(result['isError'])
        self.assertIn('found 2', result['structuredContent']['error'])
        self.assertEqual(len(self.calls), 2)

    def test_role_click_refuses_a_partial_read_with_one_link(self):
        result = self.run_flow([{'op': 'read'}, {'op': 'click', 'role': 'link'}], [
            {'complete': False, 'refs': [{'ref': 'p1:0', 'role': 'link', 'actions': ['click']}]},
        ])
        self.assertTrue(result['isError'])
        self.assertIn('needs a complete read', result['structuredContent']['error'])
        self.assertEqual(len(self.calls), 2)

    def test_discards_capture_when_the_condition_disappears(self):
        result = self.run_flow([
            {'op': 'read', 'expect_text': 'Expanded', 'wait_ms': 1000, 'screenshot': True},
        ], [{'outline': 'Expanded'}, {'outline': 'Collapsed'}])
        self.assertTrue(result['isError'])
        self.assertIn('Screenshot read lost the verified condition', result['structuredContent']['error'])
        self.assertEqual([block['type'] for block in result['content']], ['text'])


if __name__ == '__main__':
    unittest.main()
