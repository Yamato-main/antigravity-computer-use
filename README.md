# Antigravity Computer Use

> [!NOTE]
> **Computer Use 0.4.1 for Antigravity App and CLI**
>
> [Installation](#install-once-for-app-and-cli) · [Validation and known limitations](docs/VALIDATION_PR_2.md) · [Roadmap](docs/ROADMAP.md)

A plugin for Antigravity App and Antigravity CLI that operates macOS apps and browser pages from chat, including tasks that cross between them. Antigravity owns the conversation and decides what to do. The installed Cua Driver supplies window observations, browser state, and UI actions over its existing stdio MCP server. IDE support is deferred.

**Status.** Version 0.4.1 includes browser action batching, bounded readiness checks, exact browser bindings, keyboard-triggered filtering, and up to two screenshot captures per flow. Live local checks passed for filtering, form submission, and browser-to-native transfer. Inline image delivery, a short-timeout defect, and complete browsing efficiency remain unresolved; see the [latest validation report](docs/VALIDATION_PR_2.md).

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

Version 0.4.1 also repairs nested MCP metadata forwarding and isolated-browser startup and preserves snapshot coverage. Skill guidance covers schema discovery, unique task sessions, fresh action refs, and delayed results. The [latest App validation](docs/VALIDATION_PR_2.md) records the verified local workflows and remaining limitations; the [earlier validation record](docs/VALIDATION_0_4_1.md) preserves the public browsing failures that motivated this work. No general browsing speedup is established.

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

## Development and validation

The [documentation guide](docs/README.md) explains which evidence and proposals are current:

- [Latest App validation](docs/VALIDATION_PR_2.md) — installation verification, live results, and known limitations.
- [Persistent runtime design](docs/PERSISTENT_RUNTIME_DESIGN.md) — proposed future architecture and acceptance gates; implementation has not started.
- [CUA source review](docs/CUA_SOURCE_REVIEW.md) — verified mechanisms and plugin, Driver, and host responsibilities.
- [Earlier 0.4.1 validation](docs/VALIDATION_0_4_1.md) — execution repairs and public browsing failures.

Future runtime work requires an agreed task. The design proposal does not describe features available in the installed plugin.

## Contributing

See the [contribution guide](CONTRIBUTING.md) for how to agree on scope and demonstrate that a change works.

## License

This project is available under the [MIT License](LICENSE).
