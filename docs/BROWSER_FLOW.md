# Browser flow: trace comparison and manual checks

**Scope:** the existing bounded browser-flow mechanism and its manual checks. Live testing found that the 0.4.1 repairs did not deliver complete efficient browsing; see [the validation record](VALIDATION_0_4_1.md). The [persistent runtime design](PERSISTENT_RUNTIME_DESIGN.md) is the proposed successor architecture and remains unimplemented. Use the [documentation guide](README.md) before choosing future work.

This change is based on the supplied Codex and Antigravity tool traces. Both addressed the same One Piece thread, but the recordings do not establish equal coverage, identical browser state, wall time, or token usage.

| | Codex trace | Antigravity trace |
| --- | --- | --- |
| Tool overhead | 14 browser work calls, plus a completion summary and a log save. Three work calls filtered state already held by the REPL without reading the page again. Several other calls combined action and observation. | 66 logged entries: 38 plugin MCP calls, 25 file reads, and 3 commands. The final 3 entries are transcript extraction. Discovery included a directory listing and 10 individual tool schema reads. |
| Navigation | Opened the catalog directly. Followed observed links to the thread and images, returned to the thread tab, and ultimately used the page's Bottom link after scrolling and a keyboard shortcut failed to move the accessibility range. | Opened the board first, searched for the catalog, and rebound the window twice during image navigation. Near the end it issued seven separate wheel scroll calls with repeated snapshots and image reads. |
| Page state | Kept catalog and thread snapshots in REPL variables. Returned lines that matched the topic, attachment, or page region, with surrounding context when useful. Took two screenshots for visual evidence. | Made 18 semantic snapshot calls, 11 with a screenshot requested, plus 3 binds. It could query individual terms, but each new query made another Driver call and every screenshot led to a separate PNG read. |

The plugin now exposes `browser_flow` through the same MCP relay. It runs a short sequence of typed Cua operations and keeps the exact window/tab binding and one semantic snapshot per named task session. `extract` works on the saved state without a Driver call. `read` can obtain fresh state, optionally assert the URL or text, and return filtered excerpts with nearby rows. The flow returns the latest excerpt and a summary of completed steps, with separate outer and nested call counts available from the trace and `driver_calls` field. A request allows up to eight steps and 18 Driver calls with a 45-second deadline; the same Driver still checks every operation. It stops at the first failure without replaying mutations.

The workflow follows Cua's [typed browser contract](https://cua.ai/docs/cua-driver/guides/browsers): refs come from the selected tab's latest semantic snapshot; changing the page or tab invalidates the cached snapshot; read-only content refs cannot be clicked. The flow supports isolated launch, exact bind, navigation, named or ref-based click/type, and read/extract. Use direct tools for operations outside that set. No site-specific logic is built in.

## Delayed browser results

Add `wait_ms` (250–8,000 ms) to a `read` that specifies `expect_text` or `expect_url`. The flow observes immediately, then polls within the time and Driver call budgets if the condition is missing. An MCP or Driver error still stops the batch. Scoped refs and continuations belong to an observation, so use those for single reads. An optional `screenshot:true` captures and checks a fresh snapshot after readiness. A flow supports up to two screenshot reads. Their `media_offset` and `media_count` refer to the media blocks after the first text block.

For the catalog fixture in [scenario 6](VALIDATION.md#6-catalog-selection-readiness-and-inline-images), start the loopback server and send three `browser_flow` calls using one fresh session label. Use `wait_ms:5000` on each verifying read.

1. Open the isolated profile, navigate to `catalog.html`, and read for `Catalog ready: 3 discussions`.
2. Type `One Piece` into `Filter titles` with `mode:"keystrokes"`. Read for `Matching discussions: 1`, click the unique `link` role in that filtered snapshot, then read for the opening reply and `thread.html?discussion=reading-club` at the full fixture URL.
3. Click `Expand opening attachment`, then read for `Opening attachment is expanded.` with a screenshot. Click the `Later replies` link and `Expand later attachment`. Read for `Later attachment is expanded.` with a screenshot, then end. Include the later reply in `terms` to keep it in the final excerpt.

For a direct relay comparison with the previous implementation, use a fresh isolated profile for each run and the same target, text and coverage. With the previous implementation, reissue a plain `read` on a condition miss after 250 ms, 500 ms, then 1 s as needed. Click the returned link ref after filtering, and capture each image with a separate read after verifying its expansion. Count outer `browser_flow` requests and the sum of their `driver_calls` separately.

On macOS with Cua Driver 0.44.0 and disposable Brave profiles, a local MCP client exercised the relay directly. The baseline completed in 18 flow calls, 28 Driver calls, and 8.90 seconds. Three candidate runs completed in 3 flow calls each, 27–28 Driver calls, and 8.21–8.65 seconds. Each verified the selected thread, opening post, later reply, two expanded image blocks, and session cleanup. The measurement excludes model inference and host rendering. A separate direct relay run verified the same synthetic token in the browser and an exact TextEdit scratch window within one session.

An additional direct probe on the public catalog returned two topic matches and no action refs from a scoped `semantic_v2` query. A `dom_refs_v1` read returned a URL with a matching slug but no title or parent relationship, and reported truncation. The fixture route works because the page's own filter leaves a single verified result and its action ref. General title-to-link association still needs a Driver observation that preserves the relationship.

## Manual verification

Install plugin 0.4.1 or later and reconnect the MCP server using the [README](../README.md). Version 0.4.0 drops per-request MCP metadata on nested calls and can fail before opening the browser. Start the [local fixture](VALIDATION.md#prepare). In a fresh Antigravity conversation, ask it to use the following steps in one `antigravity-computer-use_cua-driver.browser_flow` call. Pick a new session label for every attempt. If Brave is the only browser, discover its running PID via the Driver and pass it as `browser_pid` on `open`.

```json
{
  "session": "flow-form-1",
  "steps": [
    {"op": "open"},
    {"op": "navigate", "url": "http://127.0.0.1:8765/"},
    {"op": "type", "name": "Test message", "text": "plugin-browser"},
    {"op": "click", "name": "Submit test message"},
    {"op": "read", "expect_text": "Submitted message: plugin-browser"},
    {"op": "end"}
  ]
}
```

Check that the visible tool result includes the submitted text, the fresh-read marker, the nested Driver call count, and successful cleanup. A missing or ambiguous action ref must stop the sequence; if it stops before `end`, end that named session separately. The one-call example includes only the workflow itself; count any separate discovery calls too.

For retained state, use `open` → `navigate` → `read` with no `query` (a `terms` filter can keep the output short). In a second call on the same session, use `extract` with different terms and confirm `driver_calls: 0` and `source: "cached"`. After a mutation, `extract` should require a new read. On a long page with an observed Bottom link, batch `click` and a fresh, filtered `read` of the latest replies; verify the destination and actual coverage. Only request a screenshot when the task needs pixels.

To measure speed, compare direct tools and flow on the same task, model, browser profile mode, and starting page in fresh conversations. Record success, elapsed time, host tool calls, nested Driver calls, and screenshots. The supplied logs motivated 0.4.0; the [0.4.1 validation record](VALIDATION_0_4_1.md) separates reproduced startup failures and live functional checks from a controlled performance benchmark. A matched before-and-after timing series has not established a general speedup.
