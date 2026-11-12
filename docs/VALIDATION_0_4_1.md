# 0.4.1 validation: browser flow startup

**Role:** current live evidence for the [persistent runtime proposal](PERSISTENT_RUNTIME_DESIGN.md), together with the [source review](CUA_SOURCE_REVIEW.md). These observations supersede earlier status assumptions while retaining the distinctions between tested candidates. The proposed runtime has not been implemented or tested. See the [documentation guide](README.md).

Recorded 2026-11-12. This is a targeted repair of failures observed in the installed 0.4.0 workflow, not a claim that everyday browsing is now fast.

## Environment and provenance

- Antigravity App 2.31.1, Gemini 3.8 Flash High, existing Turbo preset unchanged.
- Antigravity CLI 1.5.5 used only for package validation/installation; no interactive CLI task pass is claimed.
- Installed Cua Driver executable reports 0.43.2.
- Codex operated Antigravity App through its built-in Computer Use and expanded the live tool trace. Antigravity executed plugin-namespaced calls. No raw Driver run substitutes for that evidence.
- The separate Codex reference used built-in Computer Use with the in-app browser. Its browser setup and model differ from Antigravity; timings are not a controlled speedup ratio.
- Only synthetic local form data was used in the fresh reproduction. Personal browser profiles, Driver grants, global settings and permission presets were not changed.

## Observed failures and repairs

The existing public browsing transcripts reported `browser_flow` failing at its first internal request with `-32602: Missing required per-request MCP metadata`, then falling back to many direct calls. One transcript showed a 12-minute run; another showed six minutes before the user stopped it. These are diagnostic observations, not matched benchmark results.

A fresh App conversation reproduced the metadata failure on 0.4.0. The relay received the outer request's `params._meta` but discarded it while creating nested Driver calls. The repair forwards that request's metadata unchanged for each nested call. It does not cache client capabilities, fabricate missing metadata, or change Driver authorization. This matches the [MCP per-request metadata contract](https://go.sdk.modelcontextprotocol.io/protocol/).

The first live run with metadata forwarding reached `browser_prepare`, launched isolated Chrome and then exposed another failure: `open` saw three layer-0 windows and immediately refused. A follow-up diagnostic on another fresh profile saw three windows at launch and one `about:blank` window 13 seconds later. That only bounds the settling time; it does not establish a 13-second required wait.

`open` already has five observations with bounded backoff. Its loop previously stopped as soon as any candidates existed. It now continues within that same budget until exactly one candidate exists, then asks the Driver for an exact binding. A subsequent live run also caught a sole startup helper whose binding returned `browser_wrong_target_refused`. The loop now reobserves that exact prepared PID and only attempts another binding if the window ID, title or bounds changes. It never repeats an unchanged refused binding. Other refusals stop immediately. Persistent ambiguity still refuses; no title, stacking order or guessed window establishes a binding.

The first post-metadata run also preloaded eight browser schemas for a task supported by `browser_flow`. The skill now explicitly starts with that schema alone and loads direct schemas only for an observed unsupported need. Protocol errors must stop the workflow rather than trigger a long unbatched fallback.

## Reproduce the form check

Start the fixture from this repository:

```sh
python3 -m http.server 8765 --bind 127.0.0.1 --directory "$PWD/fixtures"
```

Install and reconnect as described in the README, then start a fresh App conversation. Use the same prompt for baseline and candidate:

> Use the installed antigravity-computer-use computer-use skill and its MCP server only. This is a disposable plugin regression check. I authorize a fresh Cua-owned isolated Chromium browser profile. Open http://127.0.0.1:8765/, enter metadata-repro into Test message, click Submit test message, verify Submitted message: metadata-repro from a fresh observation, and end only this task session. Use browser_flow for the known sequence. If browser_flow fails, report the exact error and stop instead of falling back to individual tools. Do not edit files or settings. Report host tool calls, nested Driver calls, and outcome.

| Attempt | Host/tool route | Calls and timing | Verified outcome |
| --- | --- | --- | --- |
| 0.4.0 baseline | App → plugin `browser_flow` | 3 file reads, 1 flow call, 1 attempted nested Driver call; UI rounded duration: 1 minute | Failed at `open`: missing per-request metadata. No browser launched; form not performed. |
| Codex reference | Built-in Computer Use → in-app browser | 3 REPL invocations: create/navigate+observe, type+submit+observe, cleanup. Reported tool runtimes total about 17.5 seconds; total wall time was not measured. | Fresh state showed `Submitted message: metadata-repro`; temporary tab closed. |
| Metadata repair only | App → plugin `browser_flow` | 1 skill + 8 schema reads, 2 flow calls, 3 nested Driver calls including cleanup; UI rounded duration: 1 minute | Metadata failure gone. Isolated browser launched, but three transient startup windows caused `open` to refuse. Form not performed; task session ended. |
| Startup diagnostic | App → plugin flow and scoped `list_windows` | 1 schema read, 3 plugin calls; UI duration: 36 seconds | Three initial windows became one about:blank window. Session ended successfully. |
| Unique-window polling candidate | App → plugin `browser_flow` | 2 flow calls, 4 nested Driver calls including cleanup; UI rounded duration: 1 minute | A sole startup window failed exact binding with `browser_wrong_target_refused`. No navigation; session ended. This exposed the need to include exact binding in the bounded startup check. |
| Metadata + bounded exact startup binding | App → plugin `browser_flow` | Skill and one schema read; 5 flow calls, 11 nested Driver attempts (10 in the successful session); UI rounded duration: 1 minute | Form submitted and exact fresh result verified; session ended. One call reused an ended label, and ref-based `type`→`click` caused a stale-ref refusal and an extra read. These are retained as failures/recovery, not presented as an efficient pass. |

After that first form pass, skill guidance was tightened again: select a fresh task label with a random/conversation suffix, and use observed names for consecutive mutating steps. The existing flow resolves names against a fresh snapshot after each mutation; it deliberately does not silently remap stale opaque refs.

## Automated checks

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
agy plugin validate --strict "$PWD/plugin"
git diff --check
```

Twenty-three tests pass, including new real-relay subprocess checks for metadata preservation across multiple nested calls, request isolation, absent metadata and refusal stop behavior. Startup tests reproduce transient multiplicity before the fix, verify zero/many-to-one recovery without real sleeps, retain refusal for persistent ambiguity, recover after a changed window observation, avoid repeating unchanged refused bindings, and stop immediately on consent refusal. Coverage tests preserve partial/complete/unknown semantics and omission reasons. Input tests verify keyboard-mode forwarding, original target/tab IDs, and rejection of unknown modes before any Driver call. New regression cases failed before their corresponding code fixes.

## Native/mixed regression

The metadata/startup candidate passed the fixture-to-TextEdit transfer through Antigravity App (UI duration: 1 minute). Operator setup created an empty scratch file and opened it in TextEdit before the task. Antigravity used the plugin to reveal a fresh token and transfer it through the native UI using one uniquely named session. Codex independently observed the matching TextEdit value afterward. No operator action substituted for a tested task step. This mixed run preceded the later coverage/input additions; it is not an additional mixed pass of those additions.

There were seven host MCP calls: three `browser_flow` calls (open/navigate/read; named click/read; end), scoped `list_windows`, initial `get_window_state`, `run_steps` with type/expect/observe, and a final native diff. The flows reported 5 + 2 + 1 nested Driver calls. The native batch's internal checks/observations are a separate counting layer; do not label all native internals as one Driver operation. No fallback route, retry, metadata error or startup refusal occurred. TextEdit remained open; the task session ended. Six schema files plus the skill were read, with native schemas loaded as that leg became necessary. The extra native diff followed a batch observation reporting no change relative to an intermediate post-write snapshot; it returned explicit matching text.

## Public browsing diagnostic

The first real browsing attempt after metadata/startup repairs still failed. In the App run, the task was to open the public anime discussion board, find an active One Piece discussion, visually inspect three images, read opening and later replies, summarize, and end its session. Codex intervened after approximately 318 seconds to stop at a checkpoint. The App reported 16 MCP calls (15 flows plus scoped window discovery), 19 nested flow Driver calls, five file reads, and zero image reads. Five flow calls were cache-only extracts. No discussion thread was opened and no requested image/reply coverage was achieved. The task session ended successfully after the stop instruction. This is an unsuccessful/intervened diagnostic, not a benchmark pass.

Observed gaps:

- The projection dropped the Driver's actual `snapshot.complete` and `snapshot.omitted` fields while showing nonexistent generic `truncated`/`snapshot_id` fields as null. The installed Driver's embedded browser guide documents complete/omitted/continuation. The projection now preserves the original coverage fields and explicitly scopes match counts to the returned snapshot. Skill/tool guidance says cached extraction cannot enlarge partial coverage.
- Bulk text insertion populated the catalog filter but did not trigger its keyboard handlers. Cua's existing `browser_type` supports `mode:"keystrokes"`; the flow now forwards that option. No synthetic event injection was added.
- The flow kept the exact binding internally but omitted `target_id` from its output. This forced discovery/rebinding before an unsupported direct operation. It now returns the Driver's original target ID along with its tab information.
- Immediate post-navigation reads twice returned empty data before page content populated. This remains an observed timing limitation; no arbitrary navigation sleep or mutation replay was added.

The separate Codex reference reached the same large discussion through board → observed Catalog link → discussion, inspected three full-size images using screenshots, and read the opening and later discussion. It used ten browser-related REPL invocations including cleanup, with one failed native accessibility scroll followed by the observed Bottom link through the built-in browser's DOM route. Its total wall time was not measured, and an accidental broad DOM output does not establish exhaustive reading coverage. The temporary tabs were closed. Browser setup and host model differ; no speedup ratio is inferred.

## Final real-task rerun: performance criterion still fails

The final App run used the same public-task prompt, App/model/Driver and isolated-profile mode after installing/reconnecting the coverage/input candidate. The prompt did not provide a thread URL. Codex intervened at about 305 seconds to stop semantic searching, make one bounded direct `dom_refs_v1` observation with the same exact target/tab/session, and end the task. Thus this is another unsuccessful/intervened diagnostic, not an autonomous benchmark pass.

- App-reported elapsed time: **355 seconds (5m55s)** from initial turn to cleanup, including a **49-second diagnostic turn**. First MCP call to cleanup: 336 seconds. Native App trace showed the initial work rounded to five minutes.
- **25 MCP calls:** 24 `browser_flow` calls and one direct `get_browser_state`. This includes one flow schema-validation error and one step-2 navigation failure. The flow calls reported **20 nested Driver calls**. These are different counting layers; cache-only extracts still require host/model round trips.
- **Zero image reads.** One viewport screenshot was offloaded but not read; no requested thread image was opened or visually inspected.
- Keyboard filtering **worked after a delay**. A subsequent fresh read showed four One Piece catalog results with reply/image counts, including the large discussion used by the Codex reference. The immediate read in the type batch still saw older results; the flow does not wait for asynchronous filter settlement.
- The task reached that discussion and read its opening plus several early replies. It did not use Bottom/read later replies and did not achieve requested image coverage. It therefore failed the requested outcome despite reaching farther than the earlier attempt.
- The direct `dom_refs_v1` diagnostic ran after the active tab had already entered the thread. It returned 300 interactive records and `truncated:true`, with href/id/name/type/placeholder/value attributes but not visible post titles/bodies. It did **not** test title-to-href association on the catalog, so no such result is claimed. Semantic observations supplied visible text while leaving some relevant links unnamed. A general efficient route combining that information remains unestablished.
- The task session ended cleanly. No browser grants, global settings, personal profiles, permission presets or repository files were changed by Antigravity.

The observed result does **not** satisfy the PR's everyday-workflow/performance merge criterion. The local repairs address demonstrated defects; they are not evidence that adding `browser_flow` solved practical browsing. No speedup ratio is claimed against either the older failed run or the different Codex host/browser route.

## Remaining validation and cleanup

Interactive CLI behavior and the latest coverage/input candidate's native/mixed behavior have not been independently rerun. Direct browser responses over the relay's text budget remain an unresolved observation issue. Image handling, long-page coverage, asynchronous page/filter readiness and excessive model round trips remain practical gaps. The next change should be chosen from this failed trace and existing Driver capabilities, not from unit-test counts or version markers.

All installed plugin files were byte-checked against the local candidate after installation. The final `browser_flow.py` SHA-256 is `79bcf6ccc0799984e70eb52f5369f50a8d86b87c7b8a494dfc76a7711cc5de16`. The loopback fixture server was stopped after the form/mixed checks. Codex reference tabs were closed; Antigravity ended each diagnostic session. The synthetic TextEdit target remains open for inspection.
