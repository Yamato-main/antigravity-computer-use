# Superseded optimization plan — historical record

**Status: superseded. Do not use this document to choose the next implementation.** The [persistent runtime design](../PERSISTENT_RUNTIME_DESIGN.md), [source review](../CUA_SOURCE_REVIEW.md) and [0.4.1 live validation](../VALIDATION_0_4_1.md) take precedence. See the [documentation guide](../README.md).

The material below describes earlier candidates. Its package/version tables, thin-relay architecture, absence-of-live-testing statements and prioritization of binding metadata are historical. Later tests repaired metadata and startup failures but still failed the full browsing task. Existing Driver capabilities and remaining integration questions are established in the newer source review; the proposed next step is a programmable persistent runtime, with prerequisite contract checks still outstanding.

Written: 2026-11-10. Implementation update: 2026-11-11.

## 0.3.0 follow-up

This historical follow-up concerned native script exposure and browser control metadata. Its referenced 0.3.0 validation file is not part of this checkout. Use the [0.4.1 validation record](../VALIDATION_0_4_1.md) for later tested candidates and blockers; the former speed draft has been removed.

## Implementation status

**2026-11-11 follow-up:** A bundled stdio MCP relay now projects the `target_id`, `binding_quality`, and up to 16 returned `tab_id` values from a successful Cua browser bind's `structuredContent` into its text result. It leaves the structured result and non-bind results intact. This addresses the specific missing-ID symptom observed in Antigravity without changing the Cua Driver or adding a second agent. Four response-contract tests pass, including multiple tabs, absent IDs, errors, and image passthrough. A read-only MCP smoke test through the relay completed initialization and `check_permissions` with exit code 0; strict plugin validation passed. Antigravity was not operated interactively after this change, as the user requested, so the browser form, native/mixed workflows, and before/after speed and token targets remain unverified. The relay is a targeted implementation of P0's adapter option; the exact source of the old text omission remains unconfirmed.

The 2026-11-11 change implements the route, observation, batching, recovery, and cleanup guidance in `plugin/skills/computer-use/SKILL.md` (P1 and the guidance portions of P2/P3). The skill now stops after one documented corrective read when browser binding omits an actionable ID. This prevents the speculative ID calls seen in the prior run if the agent follows the skill. It also uses Cua's existing text-only and diff reads and native `run_steps` interface without changing the Driver or tool exposure.

The original raw Cua MCP diagnostic, attributed separately from the plugin, confirmed that the MCP response has distinct `content` and `structuredContent` fields. A fresh isolated Brave launch returned `prepared_pid`, but `list_windows` returned no window for that PID in eight checks (including `on_screen_only:false`), so the bind payload was not obtained. The task session was ended. This does not establish which upstream component omitted the old model-visible tab ID. P4's script exposure and experimental Driver settings remain contingent on measured benefit. The installed plugin copy was not changed during this repository implementation.

The user requested no interactive Antigravity benchmark for this implementation. Accordingly, no after-change Antigravity result, speedup, token reduction, or successful browser pass is claimed. The previous live run and Codex reference below remain diagnostic evidence. The post-change manual validation sequence is `docs/VALIDATION.md`, with the bind ID and stop rule checked before measuring performance.

Local checks on 2026-11-11: `agy plugin validate --strict --json plugin` passed with one existing generic-logo note; `git diff --check` passed; all tool names used by the revised skill were present in the configured tool catalog and cached schemas. These checks prove packaging and schema compatibility, not model adherence or task completion. A direct MCP `check_permissions` read reported Accessibility and Screen Recording granted to Cua Driver; global `list_windows` showed the current ChatGPT Space, but no prepared Brave window was available for binding during the isolated diagnostic.

## Recommendation

Optimize the information and decision loop before adding execution machinery. The live run observed for this plan got stuck because browser binding exposed a summary without the tab identifier needed for the next call. Fix or conclusively diagnose that boundary first. Then reduce schema discovery, use the typed browser route, batch supported native actions, and return smaller observations without losing verification evidence.

Treat performance improvements below as hypotheses and acceptance targets, not measured speedups. For the current proposed runtime architecture and its validation gates, see [PERSISTENT_RUNTIME_DESIGN.md](../PERSISTENT_RUNTIME_DESIGN.md).

## Project model

```text
Antigravity App / interactive agy
  → plugin manifest + computer-use skill + enabled MCP tools
  → Cua executable's stdio MCP endpoint
  → shared Cua Driver and task-scoped sessions
  → exact native window / exactly bound browser tab
  → tool result delivered back to Antigravity
  → model chooses next action and verifies completion
```

Antigravity owns reasoning. This repository has no custom agent loop, backend, dependency manifest, or adapter to optimize. The package consists of:

| File | Responsibility / optimization surface |
| --- | --- |
| `plugin/plugin.json` | Version 0.1.0; one plugin identity |
| `plugin/mcp_config.json` | Direct installed executable path, `mcp` argument, 32 enabled tools |
| `plugin/skills/computer-use/SKILL.md` | Target selection, session discipline, observation, verification, routing, recovery |
| `fixtures/index.html` | Resettable synthetic form and random browser-to-native transfer token |
| `docs/VALIDATION.md` | App/CLI, native, browser, visual, mixed, denial, stale-state and interruption scenarios |
| `docs/ROADMAP.md` | Keep Antigravity in control; reuse Cua; add an adapter only for a demonstrated gap |
| `CONTRIBUTING.md` | Live Antigravity/Codex comparison and reproducible performance evidence |

The current skill already supports narrow reads, native `run_steps` with `observe`, exact browser binding, semantic browser snapshots, and checkpoint verification. It does not explicitly prefer text-only native reads or diff reads, and does not give a concise route-specific execution recipe. Its general discovery instruction may encourage unnecessary schema reading; the live run supports investigating this, but does not isolate causality.

## Evidence and limits

### Local inspection

- Host: macOS 26.6.2 (25G83); Antigravity App 2.31.0; CLI 1.5.4; installed Cua Driver app 0.44.0. The roadmap's older 0.43.2/1.5.3 checkpoint is historical, not this environment.
- Installed skill and MCP configuration under `~/.gemini/config/plugins/antigravity-computer-use/` were byte-identical to the checkout.
- Inspected cached tool schemas under `~/.gemini/antigravity/mcp/antigravity-computer-use_cua-driver/`. They corroborate advertised capabilities, not successful execution of every feature. Refresh against the running server before implementation.
- There were 62 cached JSON schemas; the 32 enabled tools totaled 96,116 bytes on disk. This is **not** a token count or proof that Antigravity injects all of them into each turn.
- `agy plugin validate --strict --json plugin` passed; only the generic-logo note remained.

### Live observation

Codex operated Antigravity through built-in Computer Use, started a fresh project conversation, and submitted a synthetic browser benchmark. The selected model was Claude Opus 4.6 (Thinking); the existing Turbo preset was left unchanged. No plugin configuration was changed. App autocomplete did not match the literal qualified slash command; the submitted prompt instead explicitly requested the installed skill and plugin MCP server. The transcript showed the skill being read and subsequent plugin-namespaced calls.

Evidence: an Antigravity App benchmark run. Reproduce it with the documented task and validation steps; local conversation identifiers are omitted.

Prompt:

> Use the installed antigravity-computer-use computer-use skill and its MCP server only for this disposable benchmark. I authorize a fresh Cua-owned temporary Chromium profile. Open http://127.0.0.1:8765/, enter plugin-browser into Test message, and click Submit test message. Verify Submitted message: plugin-browser from a fresh snapshot, then end only this task's Cua session. Report tool route and errors. Do not edit repository files or use /browser, terminal, or other MCP servers.

Observed sequence (timestamps below are UTC tool-observation times, not internal Driver timing):

| Observation | Evidence |
| --- | --- |
| Submitted 17:48:56.519 | Fresh conversation, same repository fixture served on loopback |
| By 17:49:23.485 | Multiple groups of instruction/schema reads, including skill, server instructions, session, browser actions, cleanup and window discovery |
| First launch failed | Expanded `browser_prepare` output: `refused (browser_route_unavailable): no vendor-signed system Chromium executable is available for isolated launch` |
| Recovery found Brave | Agent reported a successful separate isolated Brave launch using the running Brave PID as the executable anchor; this was not existing-profile attachment |
| Exact bind succeeded | Expanded `get_browser_state` output contained `bound target … (exact) with 1 tab(s)`; no tab ID was visible in that tool output |
| By 17:50:03.653 | Agent reported needing the tab ID and began repeated recovery reads |
| Repeated recovery | Rebinding, changing snapshot format, and a guessed `tab-0` navigation attempt did not resolve the missing identifier |
| Stop requested 17:50:30.008 | About 93.5 seconds after submission; operator requested no further guesses, exact session cleanup, and a blocker report |

This is a **failed/intervened diagnostic run**, not a successful browser timing baseline. The missing identifier may originate in Cua's text/structured result split, Antigravity's model-facing result handling, or another integration boundary. The UI summary and agent behavior are evidence of the symptom, not proof of which component drops data. Do not claim measured token savings from this run. Initial Codex UI operations also encountered transient ScreenCaptureKit `-3811` errors; those occurred before benchmark submission and are not plugin latency.

The final Antigravity report listed 16 MCP calls when its grouped four-window-discovery row is expanded: two preparations, five window listings, five browser-state calls, three failed navigation attempts, and cleanup. This is an agent-reported count, not an independently exported trace count; schema reads are additional. The report recorded `browser_tab_required` once and `browser_tab_not_found` three times. Codex independently expanded the final `end_session` call and observed `Session 'bench1' ended.` Temporary-process exit was not separately inspected. The agent's asserted structured-result root cause remains a hypothesis until P0 inspects the transport boundary.

### Codex reference on the same fixture

After the Antigravity attempt ended, Codex built-in Computer Use opened a fresh in-app browser tab at the same URL, entered the same `plugin-browser` value, clicked Submit test message and observed `Submitted message: plugin-browser` in a fresh AX state. Initial state was empty and showed `No message submitted.` The tab was then closed and an empty tab list confirmed cleanup.

- Start: 17:53:26.138 UTC; verified: 17:53:37.721 UTC; elapsed **11.583 seconds** from tab creation request to verified state, including the model gap and first-use browser documentation.
- Two CUA tool invocations through verification: create/navigate/initial observation, then type + click + final observation. A third invocation closed the tab and listed remaining tabs. These are host invocation counts, not a claim of only two underlying browser operations.
- Model identity available to this task: Codex, GPT-6-based; exact deployed variant/reasoning setting was not independently exposed. This reference reused the already initialized Codex CUA runtime and used IAB rather than Cua-owned Brave. Antigravity used Claude Opus 4.6 (Thinking), a fresh chat, MCP discovery and isolated browser setup.
- The semantic objective/data/success criterion matched; host-specific plugin instructions were replaced by Codex built-in execution. This is a single diagnostic reference with different browser/model/setup conditions, **not** a controlled speedup ratio or a complete successful plugin comparison. Token counts were unavailable for both lanes.

## Capability constraints that change the earlier speed proposal

| Proposal to qualify | Installed schema evidence and decision |
| --- | --- |
| Batch all browser operations with `run_steps` | Its action enum is native UI actions, not `browser_*`. Use it for native flows only. |
| Put browser bootstrap into `run_script` | The documented `cua.call` allowlist excludes browser tools. Do not promise this recipe works; enabling the tool alone does not add browser support. |
| Always call `start_session` | Explicit startup is optional; ordinary calls can create/reuse a named session. Keep the label, avoid a redundant startup unless initial settings or revival require it. |
| Every read returns a full PNG | Native `get_window_state` defaults to screenshots, but browser snapshots default to no screenshot; `run_steps.observe:{}` also defaults to no screenshot and a diff. Measure by route. |
| Use JPEG for every pixel action | JPEG returns no `capture_id`. Retain PNG where capture-bound targeting needs it; match coordinates to actual capture geometry. |
| Force `fast_path:on` at startup | Experimental. Scope and restoration need verification; the schema's session field alone does not prove all configuration is isolated. Test separately, never silently change shared defaults. |
| Twelve lines / 3–5× speedup are requirements | Neither has measured support. Optimize correctness and measured cost; preserve essential targeting, refusal and recovery instructions. |

## Prioritized implementation sequence

### P0 — Establish a usable result contract and baseline

1. Reproduce the missing-tab-ID failure in a fresh Antigravity conversation. Expand the tool output and record the exact input, text result, and any structured result available through supported diagnostics. Attribute raw Cua probes separately; they are not plugin passes.
2. Compare the same bind call's MCP `content` and `structuredContent` against what Antigravity receives. Check server/client versions and whether an existing output option or supported host fix exposes both target and tab identifiers.
3. Require model-visible bind output to retain `binding_quality`, `target_id`, the selectable `tab_id` list with sufficient title/URL context, and session association. Snapshot output must retain actionable refs, freshness, truncation/continuation indicators, and relevant page text. Errors must retain code and supported recovery guidance.
4. Add a bounded recovery instruction: one documented corrective attempt for a missing required field; if still absent, stop and report the boundary. Never infer opaque IDs or repeat unchanged binds indefinitely. Cleanup still runs.
5. Prefer an upstream Cua/Antigravity correction or existing output setting. Only if the host demonstrably cannot consume the needed data, propose a minimal Cua-backed result adapter as a separate architecture decision. It would project required structured fields into bounded text, preserve errors/images/session checks, and avoid a second agent loop. Do not implement it merely to shorten output.

Acceptance: the plugin can obtain the real tab ID, navigate, fill, submit, verify the exact result and clean up in a fresh conversation. A regression test for a proposed adapter must cover missing fields, multiple tabs, error results, truncation and image passthrough. No adapter work before the boundary is proven.

### P1 — Make the skill a route-specific operating protocol

Primary file: `plugin/skills/computer-use/SKILL.md`.

- Put route selection first: typed browser tools for authorized web pages; exact-window native tools for desktop work; one task session across mixed workflows.
- Discover only schemas needed for the chosen route. Reuse schemas already read within the conversation; read recovery guides only for a relevant failure. Verify whether the host already provides usable schema metadata before advising any schema reads to be skipped.
- Separate deterministic actions from observations that require reasoning. For known native sequences, use `run_steps` with one final `observe`; stop before an unknown branch or UI transition that invalidates later targets.
- Prefer one observation that proves the requested postcondition. Do not add `verify_state` plus another snapshot if the returned observation already proves it. Preserve both endpoint checks for mixed transfers; an acknowledgement is not evidence.
- Keep exact targeting, background behavior, authorized foreground escalation, refusals, stale-state recovery, and task-only cleanup in the core protocol. Move longer recipes into reference material only if the host demonstrably loads that material on demand.
- Avoid mandatory app-wide discovery when a requested app can be resolved by scoped `list_windows`. Avoid a mandatory explicit `start_session` when a unique label on ordinary calls suffices.

Acceptance: fewer schema-discovery rounds and model round trips on identical tasks, with no regression in target selection, verification or refusal behavior. Record schema reads separately from MCP calls.

### P2 — Reduce native and browser observation payloads

- Native: default to `include_screenshot:false` for trustworthy AX-accessible tasks; use one tree representation, narrow `query`/depth/element limits, and consistent scopes for `since:"latest"` diffs. Use the new snapshot ID after every read; handle reindexing and fallback status.
- Browser: prefer `semantic_v2`, bounded query/subtree reads, and continuation only when required content is outside the returned region. Preserve refs and actual values; do not return only a success boolean.
- Visual fallback: request pixels when AX/DOM is incomplete, misleading, or the task is explicitly visual. Trial 800 and 1200 pixel long-edge captures against hidden-code accuracy; enlarge or crop when needed. Use PNG for capture-bound actions and JPEG only where its semantics are sufficient.
- Do not assume query reduces backend traversal in proportion to returned text. Measure Driver duration and payload bytes separately.
- Keep errors, partial execution, freshness and cleanup outcomes visible when making responses smaller.

Acceptance: at least 50% lower returned text bytes on the repeated-state fixture, no images on successful ordinary semantic form runs, and unchanged screenshot-only hidden-code accuracy. Actual token reduction must be measured through host usage data when available; report bytes as bytes otherwise.

### P3 — Remove avoidable browser setup and retry costs

- After P0, establish a stock typed-tool baseline: prepare → scoped window discovery → exact bind → navigate → semantic snapshot → type → click → final snapshot → end session. This is roughly nine MCP operations on a clean fixture, not a promise of three calls.
- Select the intended tab from actual returned data, never the first tab by assumption. Refresh refs after navigation/new snapshots and when staleness is reported.
- Document the observed supported isolated-browser recovery through an explicit PID when default discovery cannot find a suitable executable. Check the exact installed schema and preserve fresh-profile isolation; do not turn this into an existing-profile grant.
- Reuse binding/session data within a task; do not launch or rebind at each substep. Cold browser launch and already-prepared sessions are separate measurements. Do not keep a browser session alive across tasks solely to improve benchmark numbers.
- Prefer bulk `browser_type` text insertion over per-character keystrokes where behavior permits. Use `replace:true` for setting an existing field; avoid a redundant click when typing already targets the returned editable ref.
- Use result-driven waits with bounded deadlines. Retry only when state or a documented corrective parameter changes. A consent/permission denial is a stop condition, not a routing hint.

Acceptance: zero speculative tab-ID calls, no repeated successful binding, exact result verification, and disposable browser cleanup. Count nested Driver operations separately if future host batching becomes available.

### P4 — Evaluate native scripts and optional Driver tuning separately

Possible file: `plugin/mcp_config.json`, only after an experiment justifies it.

- Trial exposing `run_script` for native loops and conditional flows. Fixed sequences remain `run_steps`; three actions alone are not a reason to require JavaScript. Use exact-window bindings, conservative call/time budgets, and return the observed value plus a compact failure summary. Reobserve after partial failure instead of replaying the whole script.
- Retain individual tools where recovery or unsupported batch operations need them. Do not assume removing tools is a permission sandbox: nested execution still follows Driver controls.
- Test tool-catalog reduction only after measuring actual host discovery/context cost. Cached schema count is not equivalent to injected prompt size.
- Do not expose `set_config` or `health_report` as routine startup work merely because they exist. Make health diagnostics failure-triggered. Evaluate `fast_path` off → shadow → guard → on on disposable targets, with restoration and stale/changed-target tests at every stage.
- Investigate cursor timing only if native Driver action duration dominates after round-trip reductions. The schema advertises a default 600 ms move floor and click dwell; this is not proof every route incurs it. Prefer session-scoped trials over global configuration changes.

Acceptance: script/tuning candidates improve measured latency and total cost beyond P1–P3, preserve interruption and denial behavior, and can be independently reverted. Otherwise omit them.

## Measurement and release gates

Run the existing validation matrix on App and interactive CLI separately. Before each candidate, keep the same model, reasoning setting, permission preset, fixture state, Driver version and installed plugin revision. Confirm the installed copy matches the candidate and start a fresh conversation. Alternate baseline/candidate runs to reduce order effects.

1. Pilot with three cold repetitions per route to find failures; then collect at least ten paired baseline/candidate runs for the primary browser and native tasks. Report median and range; reserve p95 claims for a larger sample.
2. Measure submission → verified postcondition and submission → cleanup/final reply separately. Split tool execution, model gaps, schema discovery, launch, waits/retries and user approval time where timestamps permit; do not double-count overlapping intervals.
3. Count host tool invocations, schema reads, model/tool cycles, actual nested Driver calls, full/diff reads, image dimensions/count/bytes, text output bytes, retries and refusals. Include failed runs and wasted work.
4. Record input/output/cached/reasoning tokens and cost only when host accounting exposes them. Otherwise mark unavailable; do not convert payload bytes or JPEG size into asserted billing savings.
5. Record exact verified state and whether the decoy remained unchanged. A faster failed task never counts as an improvement. Report completion rate alongside time/cost.
6. Run the same fixture in Codex built-in Computer Use as a reference. Disclose model, browser/backend, permission and orchestration differences; this is a diagnostic comparison, not a controlled model performance claim. Keep Antigravity built-in `/browser` and raw Cua as separate optional lanes.

Proposed goals after a successful baseline exists: at least 30% lower median end-to-end time and 40% lower host tool/model cycles for the targeted native workflow, and at least 40% lower measured token use when accounting exists. Browser goals must be reset from the repaired stock route: the current failed run cannot support a success-speed ratio. These goals are provisional, not guarantees.

Required regression coverage: native target plus decoy; screenshot-only hidden code and pixel action; browser form; fresh random token transferred to TextEdit; stale tokens/refs; partial batch failure; denied mutation; interrupted session and temporary-browser cleanup. Keep a long-page read scenario to catch over-narrow snapshots and continuation regressions.

Suggested future evidence row:

```text
run_id, revision, installed_hash, host/version, driver_version, model,
permission_preset, prompt, route, cold_or_warm, start, verified, cleaned_up,
schema_reads, host_calls, nested_driver_calls, retries, full_reads, diff_reads,
text_bytes, images_and_dimensions, token_usage_or_unavailable,
expected_state, observed_state, failure_boundary, operator_intervention
```

## Deliverables and stopping points

| Increment | Deliverable | Gate before next increment |
| --- | --- | --- |
| 0 | Redacted live traces, result-contract diagnosis, reproducible successful baseline | Real tab IDs reach the model; exact form result verified |
| 1 | Focused skill changes and compact route examples | Discovery/round-trip improvement with native/browser/mixed passes |
| 2 | Narrow observation and visual fallback policy | Measured output reduction, no loss of hidden-code or state accuracy |
| 3 | Browser setup/recovery improvements | No ID guessing or repeated binding; cleanup verified |
| 4 | Optional script exposure or experimental tuning | Independent measured benefit and regression coverage |
| 5 | Updated validation report, roadmap checkpoint, installed-copy verification | Repeatable App and CLI results; rollback procedure documented |

Rollback each candidate by restoring its prior skill/config revision, reinstalling the prior plugin and starting fresh conversations. Explicitly restore any experimentally changed Driver settings and clean up only the experiment's sessions. Do not introduce an adapter, replace the model, expand browser permissions, or change the shared Driver merely to meet a speed target.

## Reproduction commands

From the repository root:

```sh
agy --version
agy plugin validate --strict --json plugin
python3 -m http.server 8765 --bind 127.0.0.1 --directory fixtures
```

For a later human-led live validation, use the exact prompt above in a fresh Antigravity App conversation, expand the namespaced calls, and follow `docs/VALIDATION.md` for the other scenarios. Reload the fixture between tests, use disposable native documents, and stop the loopback server afterward. The 2026-11-11 implementation deliberately did not run that interactive validation.
