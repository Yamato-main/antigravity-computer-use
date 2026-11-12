# CUA architecture source review

**Role:** current mechanism and responsibility reference for the [persistent runtime design](PERSISTENT_RUNTIME_DESIGN.md). This review supersedes conflicting capability assumptions in the historical optimization plan. Use [0.4.1 validation](VALIDATION_0_4_1.md) for observed behavior and the [documentation guide](README.md) for precedence.

Reviewed 2026-11-12 against the installed Codex runtime and the installed Cua Driver's exposed tool contracts. This is a source/contract review, not a new live performance measurement. The persistent runtime remains a proposal.

## What the supplied screenshots establish

The central architecture is corroborated by installed code:

| Claim | Evidence and qualification |
| --- | --- |
| Dedicated persistent NodeREPL with a CUA bootstrap | The installed `@oai/cua-repl` launcher starts the executable named by `CUA_REPL_NODE_REPL_PATH`. Its environment module configures the banner and trusted browser/Sky services. The package README describes initialization once per REPL module cache and a fresh cache on reset. |
| Small execution/lifecycle tool surface | The installed unified-computer-use MCP manifest enables `js`, `js_reset`, and `turn_ended`, with a configured 25,000-token output limit for `js`. The app configures the worker before enabling this template. |
| Host cleanup notifications | The installed plugin manifest connects Interrupt, SubagentStop, and Stop hooks to `turn_ended`. This does not establish Antigravity has identical lifecycle hooks. |
| Text and image output helpers | The installed CUA display wrapper calls `nodeRepl.write` for state text and `nodeRepl.emitImage` for image bytes. These wrappers alone do not prove precisely when intermediate output becomes visible to the model or whether Antigravity supports the same streaming behavior. |
| Stateful browser accessibility revisions and a full-render option | The browser service loads `browser-accessibility.wasm.br`, retains revision pointers, and passes the previous revision to `computer_use_browser_wasm_revision_create`, with `auto` or `full` rendering. The browser API exposes `disableDiffing`. This corroborates the mechanism, not a universal payload reduction. |
| Multiple browser providers | The runtime README documents codex-app, cloud, orbit, and training modes. Chrome extension/native messaging describes a desktop provider; it is not the transport for every mode. |
| A separate native-app backend | The installed Sky client uses `MacNativePipeTransport` and the `CodexComputerUseIPC-5` API version. Browser accessibility and native-app accessibility are distinct backend paths. |

The screenshots' approximately 40,000-to-500–1,500-character reduction is not a reproduced benchmark. A configured output limit does not establish unrestricted execution: timeouts, cancellation, permissions and resource limits still matter. Freshness requirements do not force a new *model turn* for each read; a short program can read, resolve a target, act and verify in one execution.

Do not describe every screenshot detail as verified. Bundled implementation details are version-specific, and the NodeREPL engine itself was not audited here. In particular, this review does not establish an identical public Codex backend or a reusable public package contract.

### Installed package source locations

These are package-relative locations in the installed runtime and bundled plugins. They identify the reviewed artifacts without publishing the machine’s filesystem layout:

- `@oai/cua-repl/README.md`
- `@oai/cua-repl/dist/lib/js/oai_js_cua_repl/src/launch.js`
- `@oai/cua-repl/dist/lib/js/oai_js_cua_repl/src/environment.js`
- `bundled-plugins/unified-computer-use/.mcp.json`
- `bundled-plugins/unified-computer-use/.codex-plugin/plugin.json`
- `@oai/cua/dist/lib/js/oai_js_cua/src/core/display.js`
- `@oai/browser-desktop/scripts/browser-service.mjs`
- `@oai/sky/dist/project/cua/sky_js/src/targets/mac/client.js`

OpenAI also documents persistent execution and text/image observations as an integration pattern. That public guidance is separate from these installed implementation observations: [computer-use integration recipes](https://developers.openai.com/api/docs/guides/tools-computer-use-integration).

## Plugin, Driver and host responsibilities

| Capability | Where the work belongs |
| --- | --- |
| Persistent JS values, browser/native handles, programmable batches, local filtering, bounded condition waits, selected outputs | Plugin execution runtime and SDK over existing authorized Driver calls. No Driver fork inherently required. |
| Native incremental accessibility reads | Already exposed by Driver through `get_window_state` with `since` and diff/status metadata. Use it rather than implement another native AX scanner. |
| Browser incremental output | No browser `since`/delta request is documented in the cached browser schema. The plugin can retain observations and emit local comparisons, preserving coverage and fresh action refs. This reduces model payload but does not eliminate backend snapshot cost. Add Driver-side revisions/events only if that backend cost is measured as material. |
| Browser text-to-link and parent/child relationships | First test the actual catalog with existing `dom_refs_v1` and `semantic_v2` results. If neither preserves enough structure, add a typed read-only relational observation/query API inside Driver, using its existing target/tab/session checks. |
| Inline image perception | Driver and the relay already support image content. Confirm that Antigravity delivers it to Gemini vision; a visible image card or file path is not proof. This may require host integration, not a Driver patch. |
| Trusted chat identity, cancellation and end-of-task notifications | Verify Antigravity's actual MCP/lifecycle contract. Implement supported behavior in the plugin; do not assume Codex's hooks transfer to Antigravity. |

`semantic_v2` already combines accessibility, DOM, layout and viewport information; it should not be dismissed as an AX-only backend. Existing native `run_script`/`run_steps` facilities also do not establish a persistent browser REPL.

The [last validation](VALIDATION_0_4_1.md) did not prove a missing catalog relationship capability: the final DOM probe ran after entering the thread. A Driver patch remains conditional on that concrete contract test. An open-source Driver makes a narrow upstream change possible; it does not make rewriting it the first step.

## Checkpoint scope

The local 0.4.1 work repairs metadata forwarding, browser startup/binding, snapshot coverage reporting and keyboard-triggered input, with regression tests and recorded live outcomes. The public browsing task still failed its full success criteria. The [persistent runtime design](PERSISTENT_RUNTIME_DESIGN.md) and this review are documentation, not implemented performance improvements.
