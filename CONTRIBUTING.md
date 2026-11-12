# Contributing

These expectations apply to human and agent contributors alike.

> Translate engineering effort into practical performance. Theory crafting is useless if you cannot demonstrate it; never leave room to ask why an idea hasn't become working reality.

## Agree on the work

- Read the [documentation guide](docs/README.md) first. Current live evidence, the source review and the persistent runtime proposal supersede historical optimization assumptions. The proposal defines future direction; its implementation has not started and requires an agreed task.

- Start from a maintainer-assigned task or an agreed issue. The [roadmap](docs/ROADMAP.md) describes priorities. Get agreement on the outcome, scope, and acceptance criteria before starting implementation.
- Keep changes within that scope. Bring up unrelated bugs, refactors, and new ideas separately. Ask before expanding the task or changing the architecture.
- Keep Antigravity in charge of the task and build on Cua Driver. Check what the installed tools already provide before adding another layer. Identify the gap that the proposed change will close.

## Demonstrate the result

- For behavior changes, run a reproducible task through the intended Antigravity entry point and verify the result. State the host, versions, tool route, and observed outcome. Label runs through Antigravity's built-in browser, raw Cua Driver, and this plugin separately.
- For performance changes, compare before and after on the same task, with the same model and starting state where possible. Report elapsed time, tool calls, and any relevant waits or retries. Verify that the faster run still delivers the required result.
- Follow the [validation runbook](docs/VALIDATION.md) for applicable checks. Keep evidence shareable by removing private page content, credentials, and personal screenshots from traces. If a live check is blocked, give the exact blocker and steps to reproduce it, and mark that result as unverified.

In the pull request, link the agreed task, state what changed, and include the commands or steps a reviewer can use to reproduce the result.

Before publishing documentation or traces, replace user-specific filesystem paths and local conversation identifiers with portable commands and synthetic run labels. Use JST (UTC+09:00) for newly recorded timestamps and Git author/committer timezone metadata. Keep private provenance outside published files. Review commit history as well as the current files for identifying details.

## Live comparison for Codex agents

Use Codex Computer Use as the reference for how efficiently the plugin should complete real tasks. For work on plugin behavior or performance, start with a live run and work backward from what happened.

1. **Observe Antigravity App live.** Use Codex's built-in Computer Use to open Antigravity App, start a fresh chat, and submit the agreed task through the plugin. Watch the conversation and expand the tool calls as they happen. Record the executing tool, route, timestamps, retries, and verified result. Codex operates the Antigravity UI. Antigravity performs the actual task through the plugin and Cua Driver.
2. **Run the same task directly in Codex.** In a separate run, use Codex's built-in Computer Use with the same prompt, target data, starting state, and success criteria. Reset the fixture between runs as needed. Record the model, tool route, elapsed time, and result coverage for each host. Call out differences in models, permissions, or available browser access when interpreting the timings.
3. **Work backward from the first costly divergence.** Compare how the two runs find the target, read state, act, and verify. Check which mechanisms Cua Driver already supplies and whether Antigravity discovers and uses them. Fix routing, tool exposure, or skill guidance where the mechanism exists. Add code only for a demonstrated gap.
4. **Rerun the Antigravity task after the fix.** Report before-and-after time, tool calls, and verified outcomes. For browser or native routing changes, also recheck the affected mixed workflow. Keep the Codex benchmark and Antigravity plugin traces separately attributed.

Use authorized targets and disposable test data when possible. If you cannot access the App, use Codex's built-in Computer Use, or inspect the live calls, report the blocker and request a human-observed run with the same trace details.
