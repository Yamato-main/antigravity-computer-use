# Functional validation runbook

**Scope:** reusable scenarios for the existing plugin. For current observed results, use [0.4.1 validation](VALIDATION_0_4_1.md). For proposed runtime acceptance and performance gates, use [the persistent runtime design](PERSISTENT_RUNTIME_DESIGN.md). The [documentation guide](README.md) explains precedence. Passing these basic scenarios alone does not establish the desired browsing performance.

For the existing plugin, first inspect the plugin-namespaced `get_browser_state` bind result in scenario 3. It must show the exact `target_id` and the intended `tab_id` in model-visible text, and the subsequent navigation must use those returned values. If either ID is absent, stop without guessing, end the task session, and record the text result, structured result if available, and error. Compare time and tokens only after the browser form succeeds. Historical host versions and UI entry points below describe the original checks; confirm them against the intended test environment.

Run live tests in Antigravity App and interactive Antigravity CLI. Run preflight and scenarios 1–4 on each surface and record the results separately. Use fresh conversations, synthetic data, and the same chat model across comparable runs. Capture the namespaced tool calls and final observed state before ending each run. A permission denial is a valid diagnostic result. Leave the permission preset and personal browser profiles as they were.

## Prepare

1. From the root of your local checkout, start a loopback fixture server in Terminal. Use the printed port in all prompts. Stop this server with Control-C when finished.

   ```sh
   project="$PWD"
   python3 -m http.server 8765 --bind 127.0.0.1 --directory "$project/fixtures"
   ```

2. For the optional Antigravity baseline, run the next section before installing the plugin. Then install once with `agy plugin install` using the [README](../README.md). Check the shared installation in `agy plugin list` and **Customizations → Installed** in the App. Start fresh conversations on both hosts and check `/context` for the skill. The prompts below use the command shown in CLI 1.5.3 autocomplete, `/antigravity-computer-use:computer-use`. In the App, select the plugin’s `computer-use` skill in composer autocomplete and paste the text after the command. In the CLI, the interactive `/mcp` manager also shows connection status. Confirm actual execution in each conversation's tool trace. [Antigravity customization discovery](https://antigravity.google/docs/customization-discovery/), [Interactive MCP manager](https://antigravity.google/docs/mcp/#interactive-mcp-manager)
3. Use this plugin preflight prompt. Review any MCP and macOS permission prompts. Cua's Accessibility and Screen Recording grants belong to `CuaDriver.app`.

   > /antigravity-computer-use:computer-use Use the plugin MCP server to check its permissions and list only TextEdit windows. Report the server name, the permission status and the window identifiers. Leave application state as it is.

   **Pass:** the trace shows calls to `antigravity-computer-use_cua-driver` and the results are usable. An empty TextEdit list is expected when it has no windows. If discovery works but the driver is unavailable, record the exact failure, then check the installed app path and macOS grants. [Cua Driver permissions](https://cua.ai/docs/cua-driver/guides/permissions)

## Antigravity browser baseline

With the plugin absent or disabled, use the built-in `/browser` command in the App composer or CLI prompt with your usual approved browser setup. Record any remote-debugging requirement. Use a test browser profile if setup is needed.

> /browser Open http://127.0.0.1:8765/. Enter `native-browser-baseline` into Test message and click Submit test message. Verify the displayed result and report it.

**Pass:** the visible result is `Submitted message: native-browser-baseline`, and the trace attributes execution to Antigravity's browser subagent. Record this row as **Antigravity built-in**. [Antigravity browser setup](https://antigravity.google/docs/commands/browser/)

## Plugin scenarios

### 1. Native app and exact target

In TextEdit, open two disposable documents. Save one as `CUA Phase 1 Target.txt` in a scratch folder, and leave the other open as a decoy. Keep Antigravity in front during the run.

> /antigravity-computer-use:computer-use Through the TextEdit UI, append `phase-one-native` on a new line in `CUA Phase 1 Target.txt`. Work in the background, leave the other document alone, and verify the exact target's text through a fresh Cua window observation. Leave it open so I can inspect it.

**Pass:** the trace binds the named window before action and verifies it afterward. The target text matches, the decoy stays unchanged, and the native action does not bring TextEdit forward. Save or discard the scratch document yourself after inspection.

### 2. Screenshot perception and a pixel-grounded action

Manually put a fresh random code on its own line in a new TextEdit scratch document named `CUA Phase 1 Vision.txt`. Put the code in the document body only. Leave its window visible and keep the code out of the chat prompt.

> /antigravity-computer-use:computer-use Target `CUA Phase 1 Vision.txt` in TextEdit. Read the code using a Cua screenshot with `include_accessibility_tree:false`. Use a window-local pixel click from that screenshot to put the caret just after the code and append `-PIXEL` through the UI. Keep input in the background. After the action, verify the resulting line in a fresh Cua observation and report the original code and final line.

**Pass:** the trace shows screenshot-only observation before the action, the model reports the exact hidden code, and the click uses that window's image coordinates. The fresh result shows the suffix in the correct location. Record whether the model used an inline image, an Antigravity image path, or Cua's `screenshot_out_file` read through Antigravity. Run the default image path first. If it fails, retry with a smaller capture. For a file-based retry, give the agent an explicit writable scratch filename and remove that image after the test. A visible image card alone does not prove model access.

### 3. Browser page through the plugin

> /antigravity-computer-use:computer-use I authorize a fresh Cua-owned temporary Chromium profile. Use the plugin's typed browser tools to open http://127.0.0.1:8765/, enter `plugin-browser` into Test message, and click Submit test message. Verify the displayed result from a fresh snapshot before ending your Cua session. Report the browser tool route.

**Pass:** the trace uses the plugin for `browser_prepare`, exact binding, navigation, form actions, and the final browser observation. It shows `Submitted message: plugin-browser` before session cleanup. No existing browser profile is attached. If the typed route fails, record the error as a typed-route result. A separate run using Cua window controls can measure that route independently.

### 4. Browser to native app in one chat request

Create a fresh TextEdit document named `CUA Phase 1 Transfer.txt` with an empty body. Keep the fixture server running.

> /antigravity-computer-use:computer-use I authorize a fresh Cua-owned temporary Chromium profile. Open http://127.0.0.1:8765/ with the plugin, click Reveal transfer token, and read the newly displayed token from the live page. Then enter the exact token in `CUA Phase 1 Transfer.txt` through its TextEdit UI. Verify the displayed token on the page and the matching document text, use one Cua session across the two legs, and report both tool routes here. Leave TextEdit open for inspection.

**Pass:** a fresh browser observation contains `Transfer token: ` followed by 16 lowercase hex characters, and a fresh native observation shows the same token. Both legs appear under the plugin namespace in the same chat. The browser session may close after verification.

### 5. Denial, stale state, and interruption

- **Denied action.** Repeat the native scenario with a clean scratch target. Deny the first mutating MCP call. Check that the file stays unchanged and the agent reports the denial without changing routes.
- **Stale state.** In a disposable native window, have the agent take two full AX snapshots of the same target and request one harmless action with a token from the first. Cua should refuse the stale token and leave the window unchanged. Have the agent report the refusal and use a fresh token only after reobservation. If the runtime refuses the deliberate stale-token experiment before a call, record that separately.
- **Interrupted browser.** Stop a chat run after temporary browser preparation. Record any completed actions from the trace. If the browser is still open, ask the agent in the same conversation to end the exact named Cua session. Verify that the disposable browser exits. If the MCP transport has already closed, record whether the browser exits on disconnect or idle expiry. Keep the shared Driver running.

### 6. Catalog selection, readiness, and inline images

Use the same loopback server. Reload `catalog.html` for each run. The catalog loads asynchronously and filters on keyboard events. A decoy card mentions the requested title in its preview. The real title and its unnamed link occupy different branches of the same card. Each attachment renders a fresh six-character code after a delay, with the code present only in the image pixels.

> /antigravity-computer-use:computer-use I authorize a fresh Cua-owned temporary Chromium profile. Open http://127.0.0.1:8765/catalog.html and wait until the catalog is ready. Find the exact heading One Piece Reading Club and establish which link belongs to its card. Use the Filter titles field to narrow the results and verify the change. Open the observed link, verify the discussion title, read the opening post and a later reply, and expand the attachment in each post. Wait for each attachment to finish expanding, then report its code from the inline screenshot. Use the plugin only and end its disposable session. Report any missing evidence or image delivery error.

**Pass:** the trace shows `Catalog ready: 3 discussions`, `Matching discussions: 1`, and navigation via the link on the title's own card. It verifies the opening post and later reply, observes each attachment's expanded state, and returns both codes. Compare the reported codes with the corresponding images from that run. For the inline vision gate, require two correct codes without an image-file read. Record a separate result for any file-based fallback. Record outer MCP calls, nested Driver calls, readiness waits, and cleanup.

**Catalog contract check:** while the same tab is still on the catalog, compare the raw `semantic_v2` and `dom_refs_v1` structured responses with the model-visible output. Record the fields that connect the exact title to its card and link, along with coverage and any truncation. Repeat this check on the live catalog for an upstream Driver decision. The synthetic fixture makes the relationship repeatable, while the live page establishes which structures the Driver exposes there.

## Record results

Use one row per attempt. Report failures at the boundary where they occur. Examples include plugin discovery, MCP connection, Driver permission, image delivery to the model, browser attachment, action delivery, and state verification.

| Run | Provenance | Host / model | Tool or subagent | Target and mode | Verified state or exact error |
| --- | --- | --- | --- | --- | --- |
| Baseline or scenario number | Antigravity built-in / raw Cua / plugin | App or CLI, version and model | Namespaced call, including nested batch actions | Window or tab, background or foreground | Evidence from fresh observation |

For plugin passes, `/browser`, shell automation, direct file edits, and operator actions cannot stand in for any tested step. Operator setup and inspection are allowed. If troubleshooting requires a raw Cua run, use the same fixture and record it separately. Once the App has connected, the presence of cached tool schemas under `~/.gemini/antigravity/mcp/antigravity-computer-use_cua-driver/` can corroborate server discovery. The chat trace is the evidence of execution.
