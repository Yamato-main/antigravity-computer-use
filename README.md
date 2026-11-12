# Antigravity Computer Use

> [!IMPORTANT]
> **Proposed fix: a persistent, programmable CUA runtime paired with a better browser observation API. Both are necessary.**
>
> [Start with the runtime design](docs/PERSISTENT_RUNTIME_DESIGN.md). Reuse existing Driver capabilities where adequate; a Driver API change remains conditional on the observation contract tests. Implementation has not started.

A plugin for Antigravity App and Antigravity CLI that operates macOS apps and browser pages from chat, including tasks that cross between them. Antigravity owns the conversation and decides what to do. The installed Cua Driver supplies window observations, browser state, and UI actions over its existing stdio MCP server. IDE support is deferred.

**Status.** The 0.4.1 candidate repairs execution failures, but complete browsing efficiency remains unresolved. Live tests and source inspection now support a proposed persistent JS runtime over Cua Driver. That runtime has not been implemented; implementation is not starting as part of this documentation update.

## Current direction: start here

The following documents supersede the earlier optimization assumptions:

1. [Persistent runtime design](docs/PERSISTENT_RUNTIME_DESIGN.md) — proposed architecture, prerequisite checks and acceptance gates.
2. [CUA source review](docs/CUA_SOURCE_REVIEW.md) — verified mechanisms and plugin/Driver/host responsibilities.
3. [0.4.1 validation](docs/VALIDATION_0_4_1.md) — live results, repaired failures and the remaining performance gap.

See the [documentation guide](docs/README.md) for precedence and historical material, and the [roadmap](docs/ROADMAP.md) for the next agreed task. The existing browser-flow guide and functional runbook describe checks for the current plugin; they do not establish the future runtime or a measured speedup.

## Install once for App and CLI

Requires Antigravity App or interactive `agy`, Python 3.8 or later, and the standard macOS Cua Driver installation. The earlier offline checks used `agy` 1.5.3 and Cua Driver 0.43.2. Browser validation uses a signed Chromium-based browser with a disposable Driver-owned profile; a running Brave process can serve as the executable anchor. If Cua is installed at a different path, update its path in `args` in `plugin/mcp_config.json` before installing.

From the root of your local checkout, run this in Terminal. The CLI installs into Antigravity's shared user plugin directory, `~/.gemini/config/plugins/`, so App and CLI can both use the plugin across projects. If you made an earlier project-scoped copy, remove `.agents/plugins/antigravity-computer-use/` from that project first. [Antigravity plugin installation](https://antigravity.google/docs/plugins/)

```sh
project="$PWD"
agy plugin validate --strict "$project/plugin" &&
  agy plugin install "$project/plugin" &&
  agy plugin list
```

After updating, restart the plugin's `cua-driver` MCP connection in App Customizations → Computer Use → MCP → More actions → Restart, then start a fresh conversation. Browser binding/setup results should show `Cua plugin relay 0.4.1`; an absent marker indicates an old or bypassed connection. Start a fresh conversation on either surface. Existing CLI processes must also reconnect or restart.

The 0.4.1 candidate repairs nested MCP metadata forwarding and isolated-browser startup, preserves snapshot coverage and exact binding handles, and exposes Cua's keyboard input mode for live filters. Skill guidance addresses eager schema reads, reused session labels and stale-ref batches. A form check and an earlier browser/native transfer candidate passed; the later real browsing task still failed to inspect images after nearly six minutes. These repairs do not establish everyday browsing efficiency; see the [validation record](docs/VALIDATION_0_4_1.md) for candidate-specific results before considering a merge.

- **App:** Look for **Computer Use** under **Customizations → Installed**. Open the project and select the plugin’s `computer-use` skill from composer autocomplete.
- **CLI:** Run `cd "$project" && agy` and type `/antigravity-computer-use:computer-use` in the interactive prompt.

The expected MCP server name is `antigravity-computer-use_cua-driver`. Try a prompt from the [runbook](docs/VALIDATION.md) with Antigravity's normal permission prompts enabled. To remove the shared installation, use App Customizations or `agy plugin uninstall antigravity-computer-use`.

## Package

- [`plugin/`](plugin/) contains the installable manifest, Cua MCP declaration, `computer-use` skill, and a stdio relay. The relay's `browser_flow` tool batches typed browser operations and keeps the current tab and page snapshot across calls. Direct Cua tools and native `run_script` remain available.
- [Browser flow](docs/BROWSER_FLOW.md) compares the traces and shows how to check batching, retained state, and page excerpts manually.
- [`fixtures/index.html`](fixtures/index.html) supplies the local browser form and one-time transfer token used in testing.
- [`docs/VALIDATION.md`](docs/VALIDATION.md) has the live scenarios and provenance criteria.
- [`docs/README.md`](docs/README.md) identifies the current evidence, architecture proposal, supporting guides and superseded material.
- [`docs/ROADMAP.md`](docs/ROADMAP.md) summarizes the current direction and prerequisites for future implementation.
- [`docs/OPTIMIZATION_PLAN.md`](docs/OPTIMIZATION_PLAN.md) preserves a superseded investigation for historical context.

## Contributing

See the [contribution guide](CONTRIBUTING.md) for how to agree on scope and demonstrate that a change works.

## License

This project is available under the [MIT License](LICENSE).
