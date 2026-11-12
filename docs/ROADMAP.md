# Current roadmap

Status: direction documented; persistent runtime implementation has not started. Starting that work requires a future agreed task. This roadmap summarizes the [documentation guide](README.md), which identifies the current sources and superseded plans.

## Goal and evidence

Bring plugin-driven Computer Use closer to the efficient interaction pattern observed in Codex: retain useful state, execute routine action/observation groups together, and return the information needed for the next decision. Antigravity remains the agent and Cua Driver remains the authority for UI access.

The [0.4.1 validation record](VALIDATION_0_4_1.md) establishes real protocol/startup repairs and successful functional checks, with candidate-specific limitations. It also records a final public browsing diagnostic of 355 seconds and 25 MCP calls without inspecting a requested image. This is evidence of an unresolved gap, not a speedup result.

The [source review](CUA_SOURCE_REVIEW.md) corroborates persistent execution, observation revisions and text/image output mechanisms in the installed reference runtime. It identifies existing Driver capabilities and open host questions. These findings replace the earlier assumption that a thin relay and shorter instructions alone define the remaining work.

## Proposed next work, when resumed

Follow the [persistent runtime design](PERSISTENT_RUNTIME_DESIGN.md) for the full architecture and release gates:

1. **Establish observation and image contracts.** Test the actual catalog with existing browser formats for text/container/link relationships. Independently prove that inline images reach Gemini vision. These checks determine whether changes belong in an adapter, Driver or host integration.
2. **Build the smallest persistent execution slice.** One task-scoped JS worker, a small SDK over authorized Driver calls, retained values and handles, selected outputs, and explicit cancellation/reset/cleanup. Verify that filtering retained observations adds no Driver calls.
3. **Complete a representative workflow.** Cover catalog selection, discussion navigation, two images, later replies, cleanup and a browser/native transfer. Preserve freshness, scope and coverage evidence.
4. **Compare complete results.** Use matched Antigravity settings and starting state, with Codex separately attributed. Apply the design's repeated-run and call-count gates; report outer calls, nested calls, waits, model/host gaps and wall time separately.

The first two contract checks remain outstanding. No Driver fork is yet established as necessary. Do not substitute another fixed batching interface for the proposed programmable environment or claim that a screenshot proves model-visible vision.

## Existing plugin and supporting checks

The current candidate uses a stdio relay and bounded [browser flow](BROWSER_FLOW.md), with direct tools and native scripts available. The [functional runbook](VALIDATION.md) remains useful for targeting, denial, stale state, interruption and mixed workflows. It is not the complete acceptance plan for the proposed runtime.

## Historical context

The initial phase established basic plugin functionality and exposed inefficient browsing. Earlier roadmap versions are available in Git history. The [old optimization plan](OPTIMIZATION_PLAN.md) is superseded; its version tables, architecture descriptions and recommendations must not be used as current implementation guidance.
