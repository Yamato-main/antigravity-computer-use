"""Keep the Driver's keyboard input mode available inside a flow."""

import importlib.util
from pathlib import Path
import threading
import unittest


MODULE = Path(__file__).parents[1] / 'plugin/scripts/browser_flow.py'
SPEC = importlib.util.spec_from_file_location('browser_flow', MODULE)
flow = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(flow)


class BrowserInputTests(unittest.TestCase):
    def test_keyboard_mode_and_exact_binding_are_not_lost(self):
        calls = []

        def send(name, args, timeout):
            calls.append((name, args))
            if name == 'get_browser_state' and 'pid' in args:
                data = {'binding_quality': 'exact', 'target_id': 'opaque-target',
                        'tabs': [{'tab_id': 'opaque-tab', 'active': True}]}
            elif name == 'get_browser_state':
                data = {'outline': 'Search', 'action_refs': [
                    {'ref': 'p1:0', 'name': 'Search', 'role': 'textbox', 'actions': ['type']},
                ], 'complete': True, 'omitted': {}}
            else:
                data = {}
            return {'structuredContent': data, 'content': []}

        result = flow.BrowserFlows().run({'session': 'input-test', 'steps': [
            {'op': 'bind', 'pid': 99, 'window_id': 12},
            {'op': 'read'},
            {'op': 'type', 'name': 'Search', 'text': 'target topic', 'mode': 'keystrokes'},
        ]}, send, threading.Event())
        self.assertFalse(result['isError'], result)
        self.assertEqual(result['structuredContent']['completed'][0]['target_id'], 'opaque-target')
        self.assertEqual(result['structuredContent']['target_id'], 'opaque-target')
        typed = [args for name, args in calls if name == 'browser_type']
        self.assertEqual(len(typed), 1)
        self.assertEqual(typed[0]['mode'], 'keystrokes')
        self.assertEqual(typed[0]['target_id'], 'opaque-target')
        self.assertEqual(typed[0]['tab_id'], 'opaque-tab')

    def test_unknown_input_mode_fails_before_any_driver_call(self):
        def unexpected(*args):
            self.fail('Invalid flow arguments must not reach the Driver')

        result = flow.BrowserFlows().run({'session': 'input-test', 'steps': [
            {'op': 'type', 'name': 'Search', 'text': 'topic', 'mode': 'unknown'},
        ]}, unexpected, threading.Event())
        self.assertTrue(result['isError'])
        self.assertEqual(result['structuredContent']['driver_calls'], 0)


if __name__ == '__main__':
    unittest.main()
