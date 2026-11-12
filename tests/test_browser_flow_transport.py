"""Exercise nested flow calls through the actual stdio relay."""

import json
from pathlib import Path
import select
import subprocess
import sys
import unittest


RELAY = Path(__file__).parents[1] / 'plugin/scripts/cua_mcp_proxy.py'
METADATA = {
    'io.modelcontextprotocol/protocolVersion': '2026-07-28',
    'io.modelcontextprotocol/clientCapabilities': {},
    'example.com/request-context': {'opaque': ['first', {'keep': True}]},
}
SECOND_METADATA = {
    **METADATA,
    'io.modelcontextprotocol/clientCapabilities': {'experimental': {'example': {}}},
    'example.com/request-context': {'opaque': ['second']},
}


class BrowserFlowTransportTests(unittest.TestCase):
    def setUp(self):
        # The Driver validates modern metadata on every request, not just initialize.
        child = '''import json,sys
metadata = json.loads(sys.argv[1])
second_metadata = json.loads(sys.argv[2])
for raw in sys.stdin:
    msg = json.loads(raw)
    params = msg['params']
    session = params['arguments']['session']
    expected = second_metadata if session == 'second' else metadata
    if session == 'absent':
        error = 'Missing required per-request MCP metadata' if '_meta' not in params else 'Leaked metadata from a previous request'
        response = {'error': {'code': -32602, 'message': error}}
    elif params.get('_meta') != expected:
        response = {'error': {'code': -32602, 'message': 'Missing or altered per-request MCP metadata'}}
    elif session == 'refused':
        response = {'result': {'isError': True, 'structuredContent': {'refusal': {'code': 'browser_consent_required'}}}}
    else:
        name = params['name']
        data = {'binding_quality': 'exact', 'target_id': 'target', 'tabs': [{'tab_id': 'tab', 'active': True}]} if name == 'get_browser_state' and 'pid' in params['arguments'] else (
            {'snapshot': {'outline': ['ready'], 'action_refs': [], 'content_refs': []}} if name == 'get_browser_state' else {})
        response = {'result': {'content': [], 'structuredContent': data}}
    print(json.dumps({'jsonrpc': '2.0', 'id': msg['id'], **response}), flush=True)
'''
        self.process = subprocess.Popen(
            [sys.executable, str(RELAY), sys.executable, '-u', '-c', child,
             json.dumps(METADATA), json.dumps(SECOND_METADATA)],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, bufsize=1,
        )
        self.addCleanup(self.stop_relay)

    def stop_relay(self):
        self.process.stdin.close()
        try:
            self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait(timeout=5)
        self.process.stdout.close()
        self.process.stderr.close()

    def flow(self, session, metadata):
        params = {'name': 'browser_flow', 'arguments': {
            'session': session,
            'steps': [{'op': 'bind', 'pid': 12, 'window_id': 34},
                      {'op': 'read', 'expect_text': 'ready'}, {'op': 'end'}],
        }}
        if metadata is not None:
            params['_meta'] = metadata
        message = {'jsonrpc': '2.0', 'id': session, 'method': 'tools/call', 'params': params}
        # Keep stdin open until the response; EOF deliberately cancels active flows.
        self.process.stdin.write(json.dumps(message) + '\n')
        self.process.stdin.flush()
        ready, _, _ = select.select([self.process.stdout], [], [], 5)
        self.assertTrue(ready, 'Relay did not return the flow response within five seconds')
        response = json.loads(self.process.stdout.readline())
        self.assertEqual(response['id'], session)
        return response['result']

    def test_nested_calls_keep_current_request_metadata_without_reusing_it(self):
        for session, metadata in [('first', METADATA), ('second', SECOND_METADATA)]:
            with self.subTest(session=session):
                result = self.flow(session, metadata)
                self.assertFalse(result['isError'], result)
                data = result['structuredContent']
                self.assertEqual(data['driver_calls'], 3)
                self.assertEqual([step['op'] for step in data['completed']], ['bind', 'read', 'end'])
                self.assertEqual(data['completed'][1]['verified_text'], 'ready')
        missing = self.flow('absent', None)
        self.assertTrue(missing['isError'])
        data = missing['structuredContent']
        self.assertEqual(data['driver_detail']['message'], 'Missing required per-request MCP metadata')
        self.assertEqual(data['driver_calls'], 1)
        self.assertEqual(data['completed'], [])

    def test_driver_refusal_stops_without_retry_or_later_steps(self):
        result = self.flow('refused', METADATA)
        self.assertTrue(result['isError'])
        data = result['structuredContent']
        self.assertEqual(data['driver_calls'], 1)
        self.assertEqual(data['failed_step'], 1)
        self.assertEqual(data['completed'], [])
        self.assertEqual(data['driver_detail']['refusal']['code'], 'browser_consent_required')


if __name__ == '__main__':
    unittest.main()
