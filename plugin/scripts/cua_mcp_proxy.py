#!/usr/bin/env python3
"""Stdio MCP relay: expose browser observations to text-only tool consumers."""

import json
import subprocess
import sys
import threading
import uuid


RELAY_VERSION = "0.4.1"
MAX_PROJECTION_BYTES = 24000


def _prepend_text(result, text):
    content = result.setdefault('content', [])
    if not isinstance(content, list):
        return
    # Some hosts render only the first text block. Put actionable data first.
    for block in content:
        if isinstance(block, dict) and block.get('type') == 'text':
            block['text'] = text + '\n' + str(block.get('text', ''))
            return
    content.insert(0, {'type': 'text', 'text': text})


def expose_browser_binding(message, request):
    """Expose original browser metadata, including refusals, without inventing IDs.

    Preserve the actual schema, including actionable snapshot refs and content.
    Antigravity may consume only MCP text, so a count-only snapshot is unusable.
    Never infer handles or truncate opaque IDs to fit the text budget.
    """
    if request.get('method') != 'tools/call':
        return message
    params = request.get('params') or {}
    args = params.get('arguments') or {}
    name = params.get('name')
    if name != 'get_browser_state' and not (isinstance(name, str) and name.startswith('browser_')):
        return message
    result = message.get('result')
    if not isinstance(result, dict):
        return message
    structured = result.get('structuredContent')
    prefix = f'Cua plugin relay {RELAY_VERSION}; keep the same session and transport.'
    if args.get('session'):
        prefix += '\nsession: ' + json.dumps(args['session'])
    if not isinstance(structured, dict):
        # Make an unhandled contract visible; an unchanged rebind cannot fix it.
        if name == 'get_browser_state':
            _prepend_text(result, prefix + '\nNo structured browser metadata was returned. '
                          'Use IDs only if explicitly returned below; otherwise stop and '
                          'report missing IDs or action refs. Do not rebind unchanged state or use the CLI.')
        return message
    encoded = json.dumps(structured, ensure_ascii=False, separators=(',', ':'))
    if len(encoded.encode('utf-8')) > MAX_PROJECTION_BYTES:
        # Never slice a capability string or silently omit the intended tab.
        controls = {key: value for key, value in structured.items()
                    if isinstance(value, (str, int, float, bool, type(None)))
                    and len(json.dumps(value).encode('utf-8')) <= 2048}
        projection = ('Browser metadata exceeds the relay text budget; structuredContent '
                      'is preserved. No refs or content were silently truncated. '
                      'For snapshots use a narrower query/scope or a returned continuation. '
                      'Do not guess IDs or repeat an unchanged bind. Top-level controls:\n'
                      + json.dumps(controls, ensure_ascii=False, separators=(',', ':')))
    else:
        projection = 'Browser control metadata (verbatim structuredContent):\n' + encoded
    _prepend_text(result, prefix + '\n' + projection)
    return message


def main():
    from browser_flow import BrowserFlows, FlowError, TOOL

    command = sys.argv[1:] or ['/Applications/CuaDriver.app/Contents/MacOS/cua-driver', 'mcp']
    child = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                             stderr=sys.stderr.buffer)
    flows = BrowserFlows()
    pending, internal = {}, {}
    active = None
    lock = threading.Lock()
    driver_write_lock, host_write_lock = threading.Lock(), threading.Lock()
    disconnected = threading.Event()

    def encode(message):
        return (json.dumps(message, separators=(',', ':'), ensure_ascii=False) + '\n').encode()

    def to_driver(raw):
        with driver_write_lock:
            child.stdin.write(raw)
            child.stdin.flush()

    def to_host(raw):
        with host_write_lock:
            sys.stdout.buffer.write(raw)
            sys.stdout.buffer.flush()

    def key(ident):
        return (type(ident).__name__, ident)

    def response(ident, result):
        to_host(encode({'jsonrpc': '2.0', 'id': ident, 'result': result}))

    def send(name, args, timeout, request_params):
        # Use a private request ID so nested calls never appear as host tool calls.
        ident = 'cua-flow-' + uuid.uuid4().hex
        event, slot = threading.Event(), []
        with lock:
            internal[key(ident)] = (event, slot)
        params = {'name': name, 'arguments': args}
        # Modern MCP validates metadata on every request. Forward this outer
        # request's envelope unchanged; never cache or invent client metadata.
        if '_meta' in request_params:
            params['_meta'] = request_params['_meta']
        try:
            to_driver(encode({'jsonrpc': '2.0', 'id': ident, 'method': 'tools/call',
                              'params': params}))
        except OSError as error:
            with lock:
                internal.pop(key(ident), None)
            raise FlowError('Cua Driver transport closed.') from error
        if not event.wait(timeout):
            # Keep the in-flight marker until the Driver replies. Never replay a mutation.
            raise FlowError(f'{name} timed out; its effect is unknown. Wait for the Driver or reconnect.')
        if not slot:
            raise FlowError('Cua Driver disconnected; the last operation may have run.')
        reply = slot[0]
        if not isinstance(reply.get('result'), dict):
            raise FlowError(f'{name} returned an MCP error.', {'structuredContent': reply.get('error')})
        return reply['result']

    def tool_error(message):
        return {'isError': True, 'content': [{'type': 'text', 'text': message}]}

    def run_flow(ident, params, cancelled):
        nonlocal active
        def send_for_request(name, args, timeout):
            return send(name, args, timeout, params)
        try:
            result = flows.run(params.get('arguments'), send_for_request, cancelled)
        except Exception:
            result = tool_error('Browser flow failed internally. Reobserve the tab before retrying any action.')
            flows.end(None)
        with lock:
            active = None
            if not disconnected.is_set():
                response(ident, result)

    def from_host():
        nonlocal active
        try:
            for raw in sys.stdin.buffer:
                try:
                    msg = json.loads(raw)
                    method = msg.get('method')
                    params = msg.get('params') or {}
                    name = params.get('name')
                    ident = msg.get('id')
                except (ValueError, TypeError, AttributeError):
                    to_driver(raw)
                    continue
                with lock:
                    if method == 'notifications/cancelled' and active and params.get('requestId') == active[0]:
                        active[1].set()
                        continue
                    if method == 'tools/call' and 'id' in msg:
                        if active or internal:
                            response(ident, tool_error('A browser flow is still running or waiting on Cua Driver.'))
                            continue
                        if name == TOOL['name']:
                            if any(req.get('method') == 'tools/call' for req in pending.values()):
                                response(ident, tool_error('Wait for the previous Driver tool call to finish.'))
                                continue
                            cancelled = threading.Event()
                            active = (ident, cancelled)
                            threading.Thread(target=run_flow, args=(ident, params, cancelled),
                                             daemon=True).start()
                            continue
                        flows.invalidate(name, params.get('arguments') or {})
                        if name == 'end_session':
                            flows.end((params.get('arguments') or {}).get('session'))
                    if method in ('tools/call', 'tools/list') and 'id' in msg:
                        pending[key(ident)] = msg
                to_driver(raw)
        except (BrokenPipeError, OSError):
            pass
        finally:
            disconnected.set()
            with lock:
                if active:
                    active[1].set()
            with driver_write_lock:
                child.stdin.close()

    writer = threading.Thread(target=from_host, daemon=True)
    writer.start()
    try:
        for raw in child.stdout:
            try:
                msg = json.loads(raw)
                if 'id' in msg and ('result' in msg or 'error' in msg):
                    with lock:
                        ident = key(msg['id'])
                        local = internal.pop(ident, None)
                        request = pending.pop(ident, None)
                    if local:
                        event, slot = local
                        slot.append(msg)
                        event.set()
                        continue
                    if request:
                        params = request.get('params') or {}
                        name = params.get('name')
                        if request.get('method') == 'tools/list' and not params.get('cursor'):
                            tools = (msg.get('result') or {}).get('tools')
                            if isinstance(tools, list) and not any(tool.get('name') == TOOL['name'] for tool in tools):
                                tools.append(TOOL)
                                raw = encode(msg)
                        elif isinstance(name, str) and (name == 'get_browser_state' or name.startswith('browser_')):
                            expose_browser_binding(msg, request)
                            raw = encode(msg)
            except (ValueError, TypeError, AttributeError, KeyError):
                pass
            to_host(raw)
    finally:
        with lock:
            for event, _ in internal.values():
                event.set()
            internal.clear()
    writer.join(timeout=1)
    return child.wait()


if __name__ == '__main__':
    sys.exit(main())
