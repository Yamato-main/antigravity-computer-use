import copy
import importlib.util
import json
import pathlib
import subprocess
import sys
import unittest

MODULE_PATH = pathlib.Path(__file__).parents[1] / 'plugin/scripts/cua_mcp_proxy.py'
spec = importlib.util.spec_from_file_location('cua_mcp_proxy', MODULE_PATH)
proxy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(proxy)


def request(name='get_browser_state', **kwargs):
    return {'method': 'tools/call', 'params': {'name': name,
            'arguments': {'pid': 12, 'window_id': 34, 'session': 'test', **kwargs}}}


def result(structured):
    return {'result': {'content': [{'type': 'text', 'text': 'original output'}],
                       'structuredContent': structured}}


class BindProjectionTests(unittest.TestCase):
    def test_projects_original_tab_shapes_without_guessing(self):
        for tab in [{'tab_id': 'a', 'title': 'One', 'url': 'about:blank'},
                    {'id': 'opaque-a', 'title': 'One'}, {'handle': 'unknown'}]:
            with self.subTest(tab=tab):
                msg = result({'binding_quality': 'exact', 'target_id': 'bt-1', 'tabs': [tab]})
                original = copy.deepcopy(msg['result']['structuredContent'])
                proxy.expose_browser_binding(msg, request())
                text = msg['result']['content'][0]['text']
                self.assertTrue(text.startswith('Cua plugin relay 0.4.1'))
                self.assertIn(json.dumps(original, separators=(',', ':')), text)
                self.assertEqual(msg['result']['structuredContent'], original)
                self.assertTrue(text.endswith('original output'))

    def test_wrapped_binding_keeps_related_fields_together(self):
        msg = result({'data': {'target_id': 'bt-1', 'tabs': [{'tab_id': 'a'}]},
                      'source': 'cdp', 'attachment': {'status': 'attached'}})
        proxy.expose_browser_binding(msg, request())
        text = msg['result']['content'][0]['text']
        self.assertIn('"source":"cdp"', text)
        self.assertIn('"status":"attached"', text)

    def test_missing_metadata_produces_actionable_diagnostic(self):
        msg = {'result': {'content': [{'type': 'text', 'text': 'bound with 1 tab'}]}}
        proxy.expose_browser_binding(msg, request())
        text = msg['result']['content'][0]['text']
        self.assertIn('No structured browser metadata', text)
        self.assertIn('Do not rebind unchanged state', text)
        self.assertNotIn('target_id:', text)

    def test_refusals_and_next_call_are_preserved_and_visible(self):
        fields = {'refusal': {'code': 'browser_consent_required'},
                  'next_call': {'tool': 'browser_prepare', 'arguments': {'pid': 12, 'window_id': 34}}}
        for name in ['get_browser_state', 'browser_prepare']:
            msg = result(fields)
            msg['result']['isError'] = True
            original = copy.deepcopy(msg['result']['structuredContent'])
            proxy.expose_browser_binding(msg, request(name))
            self.assertTrue(msg['result']['isError'])
            self.assertEqual(msg['result']['structuredContent'], original)
            self.assertIn('"next_call":', msg['result']['content'][0]['text'])

    def test_prepare_pid_is_visible(self):
        msg = result({'prepared_pid': 123, 'profile': {'mode': 'isolated_new'}})
        proxy.expose_browser_binding(msg, request('browser_prepare'))
        self.assertIn('"prepared_pid":123', msg['result']['content'][0]['text'])

    def test_snapshot_refs_text_and_continuation_are_model_visible(self):
        fields = {'snapshot_id': 'p1', 'action_refs': [{'ref': 'p1:7', 'role': 'textbox',
                  'name': 'Test message', 'actions': ['type']}],
                  'content_refs': [{'ref': 'p1:c1', 'text': 'Submitted message: test'}],
                  'continuation': 'opaque-next'}
        msg = result(fields)
        proxy.expose_browser_binding(msg, {'method': 'tools/call', 'params': {'name': 'get_browser_state',
                                    'arguments': {'target_id': 'bt-1', 'tab_id': 'x'}}})
        text = msg['result']['content'][0]['text']
        self.assertIn('"ref":"p1:7"', text)
        self.assertIn('Submitted message: test', text)
        self.assertIn('opaque-next', text)
        self.assertEqual(msg['result']['structuredContent'], fields)

    def test_other_tools_are_unchanged(self):
        msg = result({'target_id': 'bt-1', 'tabs': [{'tab_id': 'x'}]})
        original = copy.deepcopy(msg)
        proxy.expose_browser_binding(msg, request('get_window_state'))
        self.assertEqual(msg, original)

    def test_browser_action_refusal_exposes_recovery(self):
        msg = result({'refusal': {'code': 'browser_ref_stale'}, 'next_action': 'get_browser_state'})
        proxy.expose_browser_binding(msg, request('browser_type'))
        self.assertIn('browser_ref_stale', msg['result']['content'][0]['text'])

    def test_images_preserved_and_many_tabs_not_silently_dropped(self):
        msg = result({'target_id': 'bt-1', 'tabs': [{'tab_id': str(i)} for i in range(20)]})
        image = {'type': 'image', 'data': 'abc', 'mimeType': 'image/png'}
        msg['result']['content'] = [copy.deepcopy(image)]
        proxy.expose_browser_binding(msg, request())
        self.assertEqual(msg['result']['content'][1], image)
        self.assertIn('"tab_id":"19"', msg['result']['content'][0]['text'])

    def test_budget_never_slices_identifiers_and_preserves_payload(self):
        msg = result({'target_id': 'bt-1', 'tabs': [{'tab_id': '界' * 25000}]})
        original = copy.deepcopy(msg['result']['structuredContent'])
        proxy.expose_browser_binding(msg, request())
        text = msg['result']['content'][0]['text']
        self.assertIn('exceeds the relay text budget', text)
        self.assertNotIn('界', text)
        self.assertEqual(msg['result']['structuredContent'], original)

    def test_json_rpc_error_is_unchanged(self):
        msg = {'error': {'code': -32602, 'message': 'invalid args'}}
        original = copy.deepcopy(msg)
        proxy.expose_browser_binding(msg, request())
        self.assertEqual(msg, original)

    def test_relay_forwards_notifications_and_correlates_request_ids(self):
        # Exercise the real stdio relay with a deterministic fake driver. No GUI access.
        child = '''import sys,json
for raw in sys.stdin:
    msg=json.loads(raw)
    if "id" not in msg:
        print(json.dumps(msg),flush=True)
        continue
    response={"jsonrpc":"2.0","id":msg["id"],"result":{"content":[{"type":"text","text":"original output"}],"structuredContent":{"target_id":"bt-1","tabs":[{"id":"opaque-tab"}]}}}
    print(json.dumps(response),flush=True)
'''
        messages = [dict(request(), jsonrpc='2.0', id=1),
                    {'jsonrpc': '2.0', 'method': 'notifications/initialized'},
                    dict(request('get_window_state'), jsonrpc='2.0', id='1'),
                    dict(request('browser_prepare'), jsonrpc='2.0', id=2)]
        run = subprocess.run([sys.executable, str(MODULE_PATH), sys.executable, '-u', '-c', child],
                             input=''.join(json.dumps(m) + '\n' for m in messages),
                             text=True, capture_output=True, timeout=10)
        self.assertEqual(run.returncode, 0, run.stderr)
        output = [json.loads(line) for line in run.stdout.splitlines()]
        self.assertEqual(len(output), 4)
        self.assertIn('opaque-tab', output[0]['result']['content'][0]['text'])
        self.assertEqual(output[1], messages[1])
        self.assertEqual(output[2]['result']['content'][0]['text'], 'original output')
        self.assertIn('Cua plugin relay', output[3]['result']['content'][0]['text'])


if __name__ == '__main__':
    unittest.main()
