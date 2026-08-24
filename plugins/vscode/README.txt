plugins/vscode/ — STATghost host (VS Code / Cursor)
====================================================
Updated: 2026-08-23
Status: **GO+CODE** (v0.1.0 scaffold)
Repo: jcfaria/statghost-plugins

The student menu caption is **STATghost** (never "VS Code R"). Same identity
as `plugins/cudatext/`: chrome contract, analytic side panel, clipboard
`#. STATGHOST:<CMD>` bridge. See `../../shared/CHROME.md`.

WHAT SHIPS (v0.1)
-----------------
- TypeScript port of `chrome_show.py` → `src/chromeContract.ts`
- TypeScript port of `icons_fg.py` → `src/iconsFg.ts`
- TypeScript port of `protocol.py` → `src/protocol.ts`
- Activity bar **STATghost** view with analytic grid (family bands + cells)
- Command Palette + editor title nested submenus (Send▾ Source▾ Inspect▾ Clear▾)
- Settings: `statghost.chrome.show`, `chrome.gridLabel`, `icons.fg`, `host.exe`
- Clipboard bridge for Arm/Idle, Quit, Clear, EVAL/EVAL_KEEP
- Core editor actions: send selection/above/below, inspect family, setwd, inserts

PREREQUISITES
-------------
- Node.js 20+ and npm (not present on the 2026-08-22 lab TF machine — install
  before compile/test)
- VS Code 1.85+ or Cursor (same extension API)

DEV WORKFLOW (extension host)
-----------------------------
1. cd plugins/vscode
2. npm install
3. npm run compile
4. Open this folder in VS Code → Run and Debug → **Run Extension**
   (F5). A new Extension Development Host window opens.
5. After TypeScript edits: npm run compile (or npm run watch), then
   reload the Extension Development Host (Ctrl+Shift+P → Developer: Reload Window).

PACKAGE / INSTALL
-----------------
  npm run compile
  npm install -g @vscode/vsce    # once
  npm run package                # produces statghost-vscode-0.1.0.vsix
  code --install-extension statghost-vscode-0.1.0.vsix

Or from repo root after package:
  code --install-extension plugins/vscode/statghost-vscode-0.1.0.vsix

PORTABLE VS CODE LAB (Win11 — Dropbox portable tree)
----------------------------------------------------
Path: C:\Users\jcfaria\Dropbox\&_port\VSCode
  Code.exe          — editor binary
  bin\code.cmd      — CLI (quote path: `&` in folder name)
  data\extensions\  — portable extensions dir (auto when CLI runs from bin)
  data\user-data\   — portable settings / state

Build + package (from plugins/vscode):
  powershell -File deploy_lab.ps1     # also installs Cursor lab
  — or compile + npx @vscode/vsce package --allow-missing-repository only

Reinstall into portable VS Code (PowerShell; LiteralPath for `&`):
  $port = 'C:\Users\jcfaria\Dropbox\&_port\VSCode'
  $vsix = 'C:\Users\jcfaria\Documents\Github\statghost-plugins\plugins\vscode\statghost-vscode-0.1.0.vsix'
  & "$port\bin\code.cmd" --install-extension $vsix --force

Verify:
  & "$port\bin\code.cmd" --list-extensions | Select-String statghost
  → jcfaria.statghost-vscode
  → folder: data\extensions\jcfaria.statghost-vscode-0.1.0

Open STATghost panel: launch portable Code.exe (or bin\code.cmd .), then click
the STATghost icon in the activity bar (left) — view id statghost.analyticPanel.
Palette: Ctrl+Shift+P → "STATghost: …" (e.g. Toggle Arm/Idle, Send Selection).
No --extensions-dir needed when using portable bin\code.cmd (uses data\ tree).

TESTS
-----
  npm run compile
  npm run test:unit              # node:test — chrome, icons_fg, protocol

CudaText regression (unchanged host):
  cd plugins/cudatext/cuda_statghost && python test_unit.py

MANUAL SMOKE TEST CHECKLIST
---------------------------
[ ] Extension Development Host: STATghost icon in activity bar
[ ] Side panel: HOST / SEND / SOURCE / INSPECT / CLEAR / EDIT bands
[ ] Each visible action has its own cell (no nest collapse)
[ ] Light theme: band BG slightly lifted/shaded vs sidebar
[ ] Dark theme: same check
[ ] Click Send with selection → clipboard `#. STATGHOST:EVAL …`
[ ] Command Palette → "STATghost: Toggle Arm/Idle" → ARM or IDLE token
[ ] Editor title: Send▾ submenu shows Function/Above/Below/Chunk
[ ] Settings → statghost.chrome.show → hide keys → panel refreshes
[ ] statghost.chrome.gridLabel = icon → captions hidden, hints on hover
[ ] Copy PNGs into media/icons/ → glyphs appear in cells

OUT OF SCOPE v0.1 (see BUILD_REPORT.txt)
----------------------------------------
- Full statement/function/chunk send (cuda statement.py port)
- .paths[4]/[5] source slots (paths.py port)
- Host process detection / single-instance lock (host.py D50)
- Icon PNG tint pipeline (colour Tinn glyphs copy as-is when present)
- Marketplace publish / CI

RELATED
-------
- `../../shared/CHROME.md` — multi-host chrome contract
- `../cudatext/cuda_statghost/` — reference host (Python)
- `BUILD_REPORT.txt` — deliverable summary for review
