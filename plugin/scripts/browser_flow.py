"""Bounded browser workflows over Cua Driver's typed MCP tools."""

import json
import re
import time
from urllib.parse import urlsplit

MAX_STEPS = 8
MAX_CALLS = 18
FLOW_TIMEOUT = 45
MAX_SNAPSHOT_BYTES = 512_000
MAX_EXCERPT_CHARS = 5_000
MAX_SESSIONS = 8
MAX_SCREENSHOTS = 2

STRING = {"type": "string", "minLength": 1, "maxLength": 2048}
ID = {"type": "integer", "minimum": 1}
TERMS = {"type": "array", "maxItems": 12, "items": STRING}
FILTERS = {"terms": TERMS, "limit": {"type": "integer", "minimum": 1, "maximum": 40},
           "edge": {"enum": ["first", "last"]},
           "context": {"type": "integer", "minimum": 0, "maximum": 3}}
OPS = {
    "open": ({"browser_pid": ID}, []),
    "bind": ({"pid": ID, "window_id": ID}, []),
    "select_tab": ({"tab_id": STRING}, ["tab_id"]),
    "navigate": ({"url": STRING}, ["url"]),
    "read": ({**FILTERS, "query": STRING, "scope_ref": STRING, "continuation": STRING,
              "screenshot": {"type": "boolean"}, "expect_text": STRING,
              "expect_url": STRING, "wait_ms": {"type": "integer", "minimum": 250, "maximum": 8000}}, []),
    "extract": (FILTERS, []),
    "click": ({"name": STRING, "role": STRING, "ref": STRING}, []),
    "type": ({"name": STRING, "role": STRING, "ref": STRING,
              "text": {"type": "string", "maxLength": 8192},
              "replace": {"type": "boolean"},
              "mode": {"enum": ["insert_text", "keystrokes"]}}, ["text"]),
    "end": ({}, []),
}
TOOL = {
    "name": "browser_flow",
    "description": (
        "Batch typed Cua browser operations in one named task session. "
        "Keep the exact tab binding and latest semantic snapshot across calls. "
        "Use open only for an authorized isolated browser (browser_pid anchors Brave if needed); "
        "bind with an exact pid/window_id, or without them to refresh tabs for that window. "
        "Navigate directly to known URLs. Read returns a bounded excerpt; terms filter the saved "
        "snapshot, context includes nearby rows, edge:last selects from its end. Extract filters "
        "the saved snapshot with no Driver call but cannot enlarge partial coverage. Check complete, "
        "omitted and continuation; zero cache matches do not prove absence from the page. "
        "Click/type require one exact accessible name or a returned ref; role can disambiguate. "
        "Click by role alone only when a complete latest read contains one matching action ref. "
        "Use read with expect_text or expect_url and wait_ms to verify a delayed result in the same call. "
        "A wait repeats only the read and takes any screenshot after the condition is met. "
        "Use type mode:keystrokes for search/filter inputs that require keyboard events. "
        "When a link opens a tab, bind again and select the returned tab_id explicitly. "
        "Up to two reads may request screenshots, returned in step order; end releases this task's session. "
        "Stops at the first error and never retries a mutation."
    ),
    "inputSchema": {
        "type": "object", "additionalProperties": False,
        "required": ["session", "steps"],
        "properties": {
            "session": {"type": "string", "pattern": "^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$"},
            "steps": {"type": "array", "minItems": 1, "maxItems": MAX_STEPS, "items": {
                "oneOf": [
                    {"type": "object", "additionalProperties": False,
                     "properties": {"op": {"const": op}, **properties}, "required": ["op", *required]}
                    for op, (properties, required) in OPS.items()
                ]
            }}
        }
    }
}


class FlowError(Exception):
    def __init__(self, message, upstream=None):
        super().__init__(message)
        self.upstream = upstream


def _valid(value, schema):
    if "enum" in schema:
        return value in schema["enum"]
    kind = schema["type"]
    if kind == "integer":
        return type(value) is int and schema["minimum"] <= value <= schema.get("maximum", value)
    if kind == "string":
        return isinstance(value, str) and schema.get("minLength", 0) <= len(value) <= schema["maxLength"]
    if kind == "boolean":
        return type(value) is bool
    return isinstance(value, list) and len(value) <= schema["maxItems"] and all(
        _valid(item, schema["items"]) for item in value
    )


def _validate(args):
    if not isinstance(args, dict) or args.keys() != {"session", "steps"}:
        raise FlowError("Supply only session and steps.")
    session, steps = args["session"], args["steps"]
    if not isinstance(session, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", session):
        raise FlowError("Use a short, unique named session.")
    if not isinstance(steps, list) or not 1 <= len(steps) <= MAX_STEPS:
        raise FlowError(f"Supply between 1 and {MAX_STEPS} steps.")
    screenshots = 0
    for i, step in enumerate(steps):
        op = step.get("op") if isinstance(step, dict) else None
        if not isinstance(op, str) or op not in OPS:
            raise FlowError(f"Unknown operation at step {i + 1}.")
        props, required = OPS[op]
        if not all(k in step for k in required) or not all(
            key == "op" or (key in props and _valid(value, props[key])) for key, value in step.items()
        ):
            raise FlowError(f"Invalid arguments for step {i + 1} ({op}).")
        if op == "bind" and (("pid" in step) != ("window_id" in step)):
            raise FlowError("Supply both pid and window_id, or neither to refresh.")
        if op in {"click", "type"}:
            if "ref" in step and ("name" in step or "role" in step):
                raise FlowError("Use a returned ref by itself.")
            if "ref" not in step and "name" not in step and not (op == "click" and "role" in step):
                raise FlowError("Supply an exact name or a returned ref. Click also accepts a unique role.")
        if op == "read":
            if "scope_ref" in step and "continuation" in step:
                raise FlowError("Use scope_ref or continuation for a read.")
            if "wait_ms" in step and ("scope_ref" in step or "continuation" in step or
                                     not ("expect_text" in step or "expect_url" in step)):
                raise FlowError("A wait needs an expected URL or text and a repeatable read without scope_ref or continuation.")
            screenshots += bool(step.get("screenshot"))
            if screenshots > MAX_SCREENSHOTS:
                raise FlowError(f"A flow can capture at most {MAX_SCREENSHOTS} screenshots.")
        if op == "end" and i != len(steps) - 1:
            raise FlowError("End must be the last step.")
        if op == "navigate":
            try:
                url = urlsplit(step["url"])
                valid = url.scheme in {"https", "http"} and bool(url.hostname) and url.username is None
            except ValueError:
                valid = False
            if not valid or any(ord(c) <= 32 for c in step["url"]):
                raise FlowError("Navigate with an explicit HTTP(S) URL without embedded credentials.")
    return session, steps


def _body(data, keys):
    """Accept documented fields at the top level or in the Driver's response wrappers."""
    queue = [data]
    for item in queue:
        if any(key in item for key in keys):
            return item
        for key in ("data", "binding", "browser", "snapshot"):
            if isinstance(item.get(key), dict):
                queue.append(item[key])
    return {}


def _tab_id(tab):
    value = tab.get("tab_id", tab.get("id"))
    return value if isinstance(value, str) and value else None


def _tab_view(tabs):
    return [
        {**{"tab_id": _tab_id(tab)}, **{
            key: value[:180] if isinstance(value, str) else value
            for key in ("title", "url", "active") if isinstance((value := tab.get(key)), (str, bool))
        }}
        for tab in tabs[:16]
    ]


def _page_url(data, snapshot):
    for item in (snapshot, data):
        for source in (item, item.get("page"), item.get("tab")):
            if isinstance(source, dict) and isinstance(source.get("url"), str):
                return source["url"]
    return None


def _snapshot(data):
    body = _body(data, ("outline", "refs", "action_refs", "content_refs", "continuation"))
    # Some Driver responses wrap the observation and put its controls alongside it.
    for wrapper in (data, data.get("data")):
        if isinstance(wrapper, dict) and isinstance(wrapper.get("snapshot"), dict):
            nested = wrapper["snapshot"]
            if body is nested or body is wrapper:
                return {**wrapper, **nested}
    return body


def _refs(snapshot):
    for key in ("refs", "action_refs"):
        rows = snapshot.get(key)
        if isinstance(rows, list):
            return [row for row in rows if isinstance(row, dict)]
        if isinstance(rows, dict):
            return [{"ref": key, **row} for key, row in rows.items() if isinstance(row, dict)]
    return []


def _excerpt(data, options):
    snapshot = _snapshot(data)
    outline = snapshot.get("outline", [])
    if isinstance(outline, str):
        outline = outline.splitlines()
    elif not isinstance(outline, list):
        outline = [outline]
    content = snapshot.get("content_refs", [])
    if isinstance(content, dict):
        content = [{"ref": key, **row} for key, row in content.items() if isinstance(row, dict)]
    elif not isinstance(content, list):
        content = []
    rows = outline + _refs(snapshot) + content
    lines = [row if isinstance(row, str) else json.dumps(row, ensure_ascii=False, separators=(",", ":"))
             for row in rows]
    terms = [term.casefold() for term in options.get("terms", [])]
    matches = [i for i, line in enumerate(lines) if not terms or any(term in line.casefold() for term in terms)]
    limit, context = options.get("limit", 20), options.get("context", 0)
    selected = matches[-limit:] if options.get("edge") == "last" else matches[:limit]
    indices = sorted({j for i in selected for j in range(max(0, i-context), min(len(lines), i+context+1))})
    if options.get("edge") == "last":
        indices.reverse()
    emitted, remaining = [], MAX_EXCERPT_CHARS
    for index in indices:
        # Preserve opaque refs by emitting whole rows, never sliced JSON fragments.
        if len(lines[index]) + 1 > remaining:
            break
        remaining -= len(lines[index]) + 1
        emitted.append(index)
    evidence = outline + [row[key] for row in content if isinstance(row, dict)
                          for key in ("text", "name") if isinstance(row.get(key), str)]
    return {
        "url": _page_url(data, snapshot),
        "snapshot_id": snapshot.get("snapshot_id", snapshot.get("id", data.get("snapshot_id"))),
        "matches": len(matches),
        "matches_scope": "returned_snapshot",
        "rows": [lines[i] for i in sorted(emitted)],
        "excerpt_limited": len(selected) < len(matches) or len(emitted) < len(indices),
        "complete": snapshot.get("complete"),
        "omitted": snapshot.get("omitted"),
        "continuation": snapshot.get("continuation"),
        "truncated": snapshot.get("truncated", data.get("truncated")),
    }, [row if isinstance(row, str) else json.dumps(row, ensure_ascii=False) for row in evidence]


class BrowserFlows:
    """One exact binding and latest snapshot per named task on this transport."""

    def __init__(self):
        self.sessions = {}

    def invalidate(self, name, args):
        if name in {"end_session", "check_permissions", "get_guide", "list_apps", "list_windows",
                    "get_window_state", "get_desktop_state", "verify_state"}:
            return
        if name == "start_session":
            self.end(args.get("session"))
            return
        browser_tool = isinstance(name, str) and (name == "get_browser_state" or name.startswith("browser_"))
        states = [self.sessions.get(args.get("session"), {})] if browser_tool and args.get("session") else self.sessions.values()
        for state in states:
            state.pop("snapshot", None)
            if name == "browser_prepare" or (name == "get_browser_state" and "pid" in args):
                state.pop("binding", None)

    def end(self, session):
        if session:
            self.sessions.pop(session, None)
        else:
            self.sessions.clear()

    def run(self, args, send, cancelled):
        results, images, state = [], [], {}
        calls, index = 0, None
        session = None
        deadline = time.monotonic() + FLOW_TIMEOUT

        def call(name, *, until=None, **kwargs):
            nonlocal calls
            if cancelled.is_set():
                raise FlowError("Workflow cancelled; no later steps were attempted.")
            if calls >= MAX_CALLS:
                raise FlowError("Driver call budget reached.")
            remaining = min(deadline, until if until is not None else deadline) - time.monotonic()
            if remaining <= 0:
                raise FlowError("Workflow deadline reached.")
            calls += 1
            result = send(name, {"session": session, **kwargs}, min(20, remaining))
            data = result.get("structuredContent")
            if result.get("isError") or (isinstance(data, dict) and
                    (data.get("refusal") or data.get("status") in ("refused", "error") or data.get("ok") is False)):
                raise FlowError(f"{name} refused or failed.", result)
            return data if isinstance(data, dict) else {}, result

        def bind(pid, window_id, preserve_tab=False):
            previous = state.pop("binding", {})
            state.pop("snapshot", None)
            data, result = call("get_browser_state", pid=pid, window_id=window_id)
            body = _body(data, ("target_id", "binding_quality", "tabs"))
            target, tabs = body.get("target_id"), body.get("tabs")
            if body.get("binding_quality") != "exact" or not isinstance(target, str) or not target or not isinstance(tabs, list):
                raise FlowError("Driver did not return an exact binding with target and tabs.", result)
            tabs = [tab for tab in tabs if isinstance(tab, dict) and _tab_id(tab)]
            if not tabs:
                raise FlowError("Exact binding has no usable tab IDs.", result)
            active = [_tab_id(tab) for tab in tabs if tab.get("active") is True]
            ids = {_tab_id(tab) for tab in tabs}
            old_tab = previous.get("tab_id")
            selected = old_tab if preserve_tab and old_tab in ids else (
                active[0] if len(active) == 1 else _tab_id(tabs[0]) if len(tabs) == 1 else None
            )
            state.update(window=(pid, window_id), binding={"target_id": target, "tab_id": selected, "tabs": tabs})
            return {"target_id": target, "tabs": _tab_view(tabs),
                    "tab_count": len(tabs), "selected_tab_id": selected}

        def pair():
            binding = state.get("binding", {})
            if not binding.get("tab_id"):
                raise FlowError("Bind an exact window and select its intended tab first.")
            return {key: binding[key] for key in ("target_id", "tab_id")}

        def read(options):
            target = pair()
            params = {key: options[key] for key in ("query", "scope_ref", "continuation") if key in options}
            expected_text, expected_url = options.get("expect_text"), options.get("expect_url")
            projection = {**options, "terms": [expected_text]} if expected_text and not options.get("terms") else options

            def observe(screenshot, until=None):
                state.pop("snapshot", None)
                data, result = call("get_browser_state", until=until, **target, snapshot_format="semantic_v2",
                                    include_screenshot=screenshot, **params)
                if not _snapshot(data):
                    raise FlowError("Driver did not return structured semantic page state.", result)
                if len(json.dumps(data, ensure_ascii=False).encode("utf-8")) > MAX_SNAPSHOT_BYTES:
                    raise FlowError("Snapshot exceeds the cache budget. Read with a narrower query or scope.")
                state["snapshot"] = data
                view, lines = _excerpt(data, projection)
                view["source"] = "fresh"
                problem = None
                if expected_url and expected_url != view["url"]:
                    problem = "Fresh read did not verify the expected URL."
                elif expected_text and not any(expected_text.casefold() in line.casefold() for line in lines):
                    problem = "Expected text was not present in this read; page coverage may be partial."
                elif expected_text:
                    view["verified_text"] = expected_text
                return view, result, problem

            screenshot = options.get("screenshot", False)
            if "wait_ms" in options:
                started = time.monotonic()
                until = min(deadline, started + options["wait_ms"] / 1000)
                interval, observations = 0.25, 1
                view, result, problem = observe(False, until)
                while problem and time.monotonic() + interval < until:
                    if cancelled.wait(interval):
                        raise FlowError("Workflow cancelled; no later steps were attempted.")
                    observations += 1
                    view, result, problem = observe(False, until)
                    interval = min(1, interval * 2)
                waited_ms = round((time.monotonic() - started) * 1000)
                took_screenshot = screenshot and problem is None
                if took_screenshot:
                    view, result, problem = observe(True)
                view.update(observations=observations, readiness_ms=waited_ms)
                if problem:
                    message = ("Screenshot read lost the verified condition." if took_screenshot else
                               "Readiness condition was not met.")
                    raise FlowError(f"{message} {problem}", {"structuredContent": view})
            else:
                view, result, problem = observe(screenshot)
                if problem:
                    raise FlowError(problem, {"structuredContent": view})
            if screenshot:
                blocks = [block for block in result.get("content", []) if isinstance(block, dict)
                          and block.get("type") in {"image", "resource", "resource_link"}]
                if not blocks:
                    raise FlowError("Driver did not return screenshot media.", result)
                view.update(media_offset=len(images), media_count=len(blocks))
                images.extend(blocks)
            return view

        def action_refs(step):
            op = step["op"]
            snapshot = _snapshot(state.get("snapshot", {}))
            ref = step.get("ref")
            name = step.get("name", "").casefold()
            role = step.get("role", "").casefold()
            return list(dict.fromkeys(
                row["ref"] for row in _refs(snapshot)
                if isinstance(row.get("ref"), str) and isinstance(row.get("actions"), list)
                and op in row["actions"] and
                (ref is None or row["ref"] == ref) and
                (not name or str(row.get("name", row.get("label", ""))).casefold() == name) and
                (not role or str(row.get("role", "")).casefold() == role)
            ))

        try:
            session, steps = _validate(args)
            if session not in self.sessions and len(self.sessions) >= MAX_SESSIONS:
                raise FlowError("Session cache is full. End a previous browser flow session first.")
            state = self.sessions.setdefault(session, {})
            for index, step in enumerate(steps, 1):
                if cancelled.is_set():
                    raise FlowError("Workflow cancelled; no later steps were attempted.")
                op, out = step["op"], {}
                if op == "open":
                    if state.get("launch_attempted") or state.get("window"):
                        raise FlowError("Session already has a browser. Reuse its window or end the session.")
                    params = {"pid": step["browser_pid"]} if "browser_pid" in step else {}
                    state["launch_attempted"] = True
                    data, upstream = call("browser_prepare", allow_launch=True, profile={"mode": "isolated_new"}, **params)
                    pid = _body(data, ("prepared_pid",)).get("prepared_pid")
                    if type(pid) is not int or pid <= 0:
                        raise FlowError("Isolated launch did not return a prepared PID. End this session before retrying.", upstream)
                    state["prepared_pid"] = pid
                    attempted_windows, last_binding_error = set(), None
                    for attempt in range(5):
                        windows, _ = call("list_windows", pid=pid)
                        candidates = [w for w in windows.get("windows", [])
                                      if isinstance(w, dict) and w.get("pid") == pid and
                                      w.get("layer") == 0 and type(w.get("window_id")) is int]
                        # Chromium can expose transient startup windows, even a
                        # sole helper before its main window is ready. Reobserve
                        # within the same budget and require an exact binding.
                        if len(candidates) == 1:
                            window = candidates[0]
                            signature = json.dumps([window.get(key) for key in
                                                    ("window_id", "title", "bounds")], sort_keys=True)
                            if signature not in attempted_windows:
                                attempted_windows.add(signature)
                                try:
                                    out = bind(pid, window["window_id"])
                                    break
                                except FlowError as error:
                                    detail = (error.upstream or {}).get("structuredContent", {})
                                    refusal = detail.get("refusal", {}) if isinstance(detail, dict) else {}
                                    if not isinstance(refusal, dict) or refusal.get("code") != "browser_wrong_target_refused":
                                        raise
                                    last_binding_error = error
                        if attempt < 4:
                            cancelled.wait(0.35 * (attempt + 1))
                    else:
                        if len(candidates) == 1 and last_binding_error:
                            raise last_binding_error
                        ids = [window["window_id"] for window in candidates]
                        raise FlowError(f"Prepared PID {pid}: expected one browser window; got {ids}. Bind an exact window or end the session.")
                elif op == "bind":
                    window = (step["pid"], step["window_id"]) if "pid" in step else state.get("window")
                    if not window:
                        raise FlowError("Supply the observed pid and window_id for the first bind.")
                    out = bind(*window, preserve_tab="pid" not in step)
                elif op == "select_tab":
                    binding = state.get("binding", {})
                    if step["tab_id"] not in {_tab_id(tab) for tab in binding.get("tabs", [])}:
                        raise FlowError("Tab is not in this session's last exact binding. Refresh tabs first.")
                    binding["tab_id"] = step["tab_id"]
                    state.pop("snapshot", None)
                elif op == "navigate":
                    target = pair()
                    state.pop("snapshot", None)
                    call("browser_navigate", **target, url=step["url"])
                elif op == "read":
                    out = read(step)
                elif op == "extract":
                    if "snapshot" not in state:
                        raise FlowError("No current cached snapshot. Read the selected tab first.")
                    out, _ = _excerpt(state["snapshot"], step)
                    out["source"] = "cached"
                elif op in {"click", "type"}:
                    target = pair()
                    if "name" not in step and "ref" not in step and (
                            _snapshot(state.get("snapshot", {})).get("complete") is not True):
                        raise FlowError("Click by role alone needs a complete read of the intended scope.")
                    matches = action_refs(step)
                    if not matches and "name" in step:
                        read({"query": step["name"]})
                        matches = action_refs(step)
                    if len(matches) != 1:
                        raise FlowError(f"{op} requires one matching action ref from the latest read; found {len(matches)}.")
                    state.pop("snapshot", None)
                    params = {"text": step["text"], "replace": step.get("replace", True)} if op == "type" else {}
                    if op == "type" and "mode" in step:
                        params["mode"] = step["mode"]
                    data, upstream = call(f"browser_{op}", **target, ref=matches[0], **params)
                    dialog = _body(data, ("dialog",)).get("dialog")
                    if isinstance(dialog, dict) and dialog.get("present"):
                        raise FlowError("Browser dialog opened; inspect it with the direct dialog tool.", upstream)
                    if data.get("effect") == "unverifiable":
                        out["effect"] = "unverifiable"
                elif op == "end":
                    call("end_session")
                    self.end(session)
                    state = {}
                if op in {"read", "extract"}:
                    for previous in reversed(results):
                        if "rows" in previous:
                            previous.pop("rows")
                            previous["excerpt_replaced"] = True
                            break
                results.append({"step": index, "op": op, **out})
            response = {"session": session, "driver_calls": calls, "completed": results}
        except FlowError as error:
            response = {"session": session, "driver_calls": calls, "completed": results,
                        "failed_step": index, "error": str(error),
                        "prepared_pid": state.get("prepared_pid")}
            if error.upstream:
                # Keep original refusal details, without replaying large page or media blobs.
                data = error.upstream.get("structuredContent")
                if isinstance(data, dict) and len(json.dumps(data)) <= 5000:
                    response["driver_detail"] = data
                texts = [b.get("text", "") for b in error.upstream.get("content", [])
                         if isinstance(b, dict) and b.get("type") == "text"]
                if texts:
                    response["driver_message"] = texts[0][:1200]
        if state.get("binding"):
            response["target_id"] = state["binding"].get("target_id")
            response["selected_tab_id"] = state["binding"].get("tab_id")
        return {"isError": "error" in response, "structuredContent": response,
                "content": [{"type": "text", "text": json.dumps(response, ensure_ascii=False,
                             separators=(",", ":"))}, *images]}
