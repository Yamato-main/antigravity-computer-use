# PR #2 local installation and App validation

Recorded 2026-11-13 JST (UTC+09:00). This record describes the pre-merge installation and testing of [PR #2](https://github.com/Yamato-main/antigravity-computer-use/pull/2). The proposed runtime was not implemented.

## Candidate and environment

- Baseline: `e45f5a3407c1d49ae7fbb2eee9283d836d3399e2` (`codex/dev`). The installed baseline's `browser_flow.py` matched the previously recorded SHA-256, `79bcf6ccc0799984e70eb52f5369f50a8d86b87c7b8a494dfc76a7711cc5de16`.
- Candidate: `a7eff5c311cdd0c5a5ba6190097b22d91bdf5930`, tested on a separate local branch. The development branch was not advanced.
- macOS; Antigravity App 2.31.2; Gemini 3.8 Flash Medium; CLI 1.5.6; Cua Driver bundle version 0.43.2; Python 3.14.3. These differ from the PR author's direct-relay environment, which reported Driver 0.44.0.
- The App's existing permission preset was left unchanged. Antigravity used fresh Cua-owned isolated browser profiles. Codex operated and observed Antigravity through built-in Computer Use; operator actions did not perform Antigravity's tested browser steps.
- Both App runs used the candidate's loopback fixtures, served on `127.0.0.1:8765`. The same task prompt, model, host and profile mode were used for the baseline/candidate comparison.

The old installation was backed up before updating. `agy plugin install` replaced the shared installation, then the App's plugin MCP connection was restarted and a fresh conversation started. All five installed package files were byte-compared with the candidate: manifest, MCP configuration, relay, browser flow and skill. The candidate flow hash is `2af3bcbb8c304313aaf917ae83fea1ded66c95a646716572000a9fd27944c581`; its skill hash is `c2a7f1a362a4dcded613329720083a66d870e94daa40bf87d6df761f477ca3c8`. Both still declare version 0.4.1, so the version marker alone cannot distinguish these installations. The refreshed App tool schema included `wait_ms`, role-only clicks and two screenshot reads.

## Automated checks

From the candidate checkout:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
agy plugin validate --strict "$PWD/plugin"
git diff --check codex/dev...HEAD
```

All 29 tests passed. Strict plugin validation and the diff check passed. Validation reported an informational missing-logo notice.

## Live catalog comparison

In separate fresh App conversations, use the installed skill and plugin MCP server only. Authorize a disposable isolated profile, open `http://127.0.0.1:8765/catalog.html`, wait for catalog readiness, find the exact One Piece Reading Club heading, narrow the title filter through keyboard events, and follow the observed matching card link. Read the opening post and later reply, expand their attachments, wait for expansion and report both six-character codes from inline screenshots. Disallow image-file reads and alternate automation routes; report missing image delivery instead. End the task session and report outer calls, nested calls, readiness and elapsed time. This added constraint deliberately tests the inline vision gate rather than a file-reader fallback.

| Run | Route | Outer flow calls | Nested flow Driver calls | Verified result |
| --- | --- | ---: | ---: | --- |
| Baseline | App → plugin `browser_flow` | 14 | 22 | Filtered to one discussion, read both posts, expanded both attachments and ended session. Inline codes unavailable. |
| PR #2 | App → plugin `browser_flow` | 11 | 26 | Same text/expansion coverage and session end; one response captured two screenshots. Inline codes unavailable. |
| Codex reference | Built-in Computer Use → in-app browser | 9 browser-related REPL calls including cleanup | Not applicable | Verified filtered result, both posts, both expanded images and their pixel codes; closed temporary tab and verified empty tab list. |

The App displayed rounded work durations of three minutes for the baseline and two minutes for the candidate. Its final summaries estimated approximately three minutes and 2m35s respectively; these are host/model-reported estimates, not a controlled wall-time series. Counts exclude skill/schema file reads and keep nested Driver work separate. No speedup ratio is claimed: both App runs failed the requested inline image outcome, and this is only one run per installation.

The candidate's initial readiness read reported four observations and 1,871 ms. Its later attachment read used the full `Later attachment is expanded.` condition with `wait_ms:5000`, reported three observations and 822 ms, and returned the second capture in the same flow as the first. The completed trace contained eleven flow calls and a successful final `end` step.

One earlier candidate read used the weak condition `expect_text:"expanded"`. That substring also matched button state text such as `expanded=false`, so it captured before expansion completed. A later fresh read verified the full expansion sentence. This is a model-chosen predicate limitation; use the complete rendered-state indicator from the runbook rather than the ambiguous substring.

Both App runs reported that screenshot content was offloaded to `media_0.png` (and `media_1.png` for the two-capture response), leaving no inline pixels available to the model. Neither read those files. Neither returned an attachment code. Returning two captures therefore does not establish Antigravity inline image perception. The separately attributed Codex reference read `7RPT6E` and `S8FLSA` from its own run's images; codes are randomized per run and are not expected to match the App's images.

## Role-only selection, form and native transfer

A separate App check explicitly requested the new readiness and role-only mechanisms, followed by the existing form/native workflow. Operator setup created and opened one empty scratch document, `CUA PR2 Transfer.txt`. Permissions and exact native-window discovery went through the plugin.

The first turn spent approximately three rounded UI minutes in permission/guide/session preflight and opened a preliminary browser session without completing the workflow. An operator follow-up directed it to read the installed skill/schema and continue the specified steps. Treat the continuation as an intervened functional check, not an autonomous benchmark or a timing pass.

The continuation verified:

- `Catalog ready: 3 discussions`: four observations, 1,883 ms.
- Keyboard filtering followed by `Matching discussions: 1`: three observations, 813 ms; complete snapshot.
- `click` with only `role:"link"` succeeded. A subsequent binding refresh identified the active One Piece Reading Club tab and its expected discussion URL.
- Form submission returned `Submitted message: pr2-regression` from a fresh verifying read.
- The browser generated the synthetic token `acd6da7958ec0361`. Under the same explicit task session, plugin `get_window_state` identified the exact scratch window, and `run_steps` entered the token through its native text field. The post-action observation contained the same value. Codex independently observed matching document text afterward.
- The final task session ended successfully; TextEdit remained open for inspection. The implicit preflight session was explicitly ended as well.

A final cleanup-only request ended the preliminary browser session. The plugin returned an explicit successful `end_session` result. All task-created sessions were ended; no additional browser was launched for cleanup.

The completed functional sequence used seven `browser_flow` calls with **23** nested Driver calls (`12 + 1 + 1 + 2 + 4 + 2 + 1`), verified by expanding the App tool trace. Permissions, guide reads, preliminary session work, native calls and final preliminary-session cleanup are additional work. The agent's summary incorrectly totaled these seven flows as 22 and did not include all preliminary work in its overall count; use the observed per-call values rather than that summary. Native `run_steps` internals are a separate counting layer.

## Readiness timeout diagnostic

Independent scrutiny reproduced an early timeout with the existing fake clock and Driver helpers from `tests/test_browser_flow_readiness.py`. No real browser, sleep or UI operation was involved.

| `wait_ms` | Condition becomes ready | Observation times | Reported elapsed | Result |
| ---: | ---: | --- | ---: | --- |
| 500 | 200 ms | 0, 250 ms | 250 ms | Success; trailing cleanup executed. |
| 500 | 400 ms | 0, 250 ms | 250 ms | Readiness error; trailing cleanup not executed. |

To reproduce, use `Clock`, patch the flow module's `time.monotonic` to that clock, and have the fake `get_browser_state` return `Loading` until clock time 0.4 seconds, then `Ready`. Run `bind` → `read(expect_text="Ready", wait_ms=500)` → `end`. The result reports `observations:2`, `readiness_ms:250`, and `Readiness condition was not met. Expected text was not present in this read; page coverage may be partial.`

The polling loop requires the next full backoff interval to fit strictly before the deadline. It can stop before the supplied budget and miss readiness within it. This remains a candidate defect to fix and cover with a condition-near-deadline regression. Failure stopping before `end` is the existing stop-on-error behavior; callers must separately clean up failed sessions. No implementation change was made during this validation task.

Runnable reproduction from the candidate checkout:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
import runpy
from unittest.mock import patch

helpers = runpy.run_path('tests/test_browser_flow_readiness.py')
flow, clock = helpers['flow'], helpers['Clock']()
reads = []

def send(name, args, timeout):
    if 'pid' in args:
        data = {'binding_quality': 'exact', 'target_id': 'target',
                'tabs': [{'tab_id': 'tab'}]}
    elif name == 'get_browser_state':
        reads.append(round(clock.now * 1000))
        data = {'outline': 'Ready' if clock.now >= 0.4 else 'Loading'}
    else:
        data = {}
    return {'structuredContent': data, 'content': []}

with patch.object(flow.time, 'monotonic', lambda: clock.now):
    result = flow.BrowserFlows().run({'session': 'deadline-check', 'steps': [
        {'op': 'bind', 'pid': 1, 'window_id': 2},
        {'op': 'read', 'expect_text': 'Ready', 'wait_ms': 500},
        {'op': 'end'},
    ]}, send, clock)
print('read times (ms):', reads)
print('elapsed (ms):', round(clock.now * 1000))
print(result['structuredContent'])
assert result['isError'] and reads == [0, 250] and clock.now == 0.25
PY
```

## Limits

This fixture does not establish general title-to-link association on a public catalog. The live contract probe, inline image host integration, and proposed persistent runtime remain separate work. Interactive CLI scenarios, intentional permission denial and native pixel-click perception were not rerun as part of this PR-focused App check. No GitHub review or PR comment was posted during validation.

## Promotion decision

After reviewing these results, the maintainer authorized promotion through `codex/dev` into `main` as an incremental improvement. Inline image perception and the readiness timeout defect remain documented follow-up work; promotion does not establish a complete browsing performance pass. The validation report accompanies the tested code, with no further plugin implementation changes.
