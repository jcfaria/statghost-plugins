# STATghost — Notepad++ host (strategic study)

**Status:** GO+CODE (lab v1 — VP-NPP-1/2/3/6)  
**Updated:** 2026-08-24  
**Canonical chrome contract:** `shared/CHROME.md`  
**Full packs:** `plugins/notepadpp/w_todo/` (SAP 01, CPR 02, EN ↔ PT)

---

## Executive summary

Notepad++ is a viable **third host** for the STATghost chrome contract. Maximum
visual flexibility (docking side panel, toolbar icons, dark mode) requires a
**native Unicode C++ plugin DLL** using `PluginInterface` +
`DockingDlgInterface`. PythonScript, NppExec, and external tools are useful
for lab spikes only — they cannot reliably deliver the analytic keypad or
theme parity.

**Lab v1 (2026-08-24):** C++ Unicode DLL under `plugins/notepadpp/statghost-npp/`
(menu nests, dock grid, clipboard EVAL). Remaining: VP-NPP-4 toolbar polish,
VP-NPP-5 Config UI, VP-NPP-7 three-host golden, VP-NPP-8 Plugin Admin.
Unify contract tests and finish `shared/` extract (VP-CH-5).

---

## Plugin models (N++)

| Model | Role | STATghost fit |
|-------|------|---------------|
| **C++ DLL** (`isUnicode`, `getFuncsArray`, `beNotified`) | Official path; Plugin Admin distribution | **Primary (recommended)** — menu, toolbar, dock panel, config dialog |
| **Object Pascal DLL** (Delphi/Lazarus, `cdecl` exports) | Documented in N++ manual; community template [delphiplugintemplate](https://github.com/rdipardo/delphiplugintemplate); examples DBGp, NppCalc | **Viable alternative** — same Win32 docking API; no official template; owner chooses at VP-NPP-0 |
| **DockingDlgInterface** + `NPPM_DMMREGASDCKDLG` | Registered dock/float panel persisted in `config.xml` | **Required** for analytic keypad analogue |
| **NPPM_ADDTOOLBARICON_FORDARKMODE** | Light + dark toolbar glyphs (v8.0+) | Compact bar icons |
| **NPPM_GETDARKMODECOLORS** + `NPPN_DARKMODECHANGED` | Theme bridge for dialogs | Manual `ThemeBridge`; no auto token map |
| **PythonScript** | Script commands, optional `WinDialog` | **Reject** for production chrome — dock theming bugs, no official nest toolbar |
| **NppExec** | Run external commands | Bridge helper only (clipboard), not UI |
| **NPPM_MSGTOPLUGIN** | Inter-plugin IPC | Out of scope unless future split DLL |

The host/plugin boundary is **C ABI** (`extern "C"` / `cdecl`); Rust or other
languages are possible. **Object Pascal** (Delphi/Lazarus) is documented in the
N++ user manual and proven in production plugins — same DLL contract, community
template only. C++ remains the path with the most official examples
(npp-plugins/plugintemplate, NppPluginTemplate, dark-mode helpers).

---

## Visual flexibility scorecard (0–5)

| Surface | C++ DLL | PythonScript | Notes |
|---------|---------|--------------|-------|
| Plugins menu (STATghost group) | 5 | 3 | `getFuncsArray`; nests via submenu handle or grouped commands |
| Settings / config UI | 4 | 2 | No VS Code-style settings tree — custom modal or docked prefs dialog |
| Main toolbar icons | 4 | 1 | Flat icons per command; **no native nested toolbar** (Tinn-style ▾) |
| Side dock panel | 5 | 2 | `DockingDlgInterface`; custom owner-draw grid |
| Dark / light theme | 3 | 2 | API since v8.4; recursive child controls need manual pass |
| DPI / font scaling | 3 | 2 | Win32 dialog units; test 100%/125%/150% |
| Icons 16/24/32 | 5 | 3 | Toolbar struct + bitmap buttons in dock client |
| Custom cell grid (CHROME) | 5 | 2 | Owner-draw or button grid in `HWND` client |

**Compromise vs CudaText / VS Code:** toolbar nests collapse to **menu-only
children** or **flat toolbar** (parent icon = primary action). Side panel can
match `grid_plan()` 1:1 with owner-draw.

---

## Mapping to `shared/CHROME.md`

| Contract surface | CudaText | VS Code | Notepad++ (planned) |
|------------------|----------|---------|---------------------|
| Menu nests | `chrome.py` | `package.json` submenus | Plugins ▶ STATghost ▶ nested `FuncItem` groups |
| Compact toolbar | `DATA1` workbar | Command palette + optional toolbar | `NPPM_ADDTOOLBARICON_FORDARKMODE` — flat icons |
| Analytic side panel | `AnalyticPanel` dlg | `panelProvider.ts` webview | `DockingDlgInterface` + owner-draw grid |
| Config `chrome.show` | `config.py` tree | `settings.json` | Modal checklist or docked prefs page |
| Theme automatic | `theme tokens` | `themeBridge.ts` CSS vars | `NPPM_GETDARKMODECOLORS` → `ThemeBridge` |
| Registry | `chrome_show.py` | `chromeContract.ts` | Import generated headers from shared contract (VP-CH-5) |

---

## Language choice

**Use C++ Unicode DLL** for the production host.

Justification:

1. Only path with **supported** docking + toolbar + notification API.
2. Dark mode hooks are documented for native HWND dialogs.
3. Analytic grid needs custom layout (bands + 3-col cells) — same class of
   work as CudaText `dlg_proc`, not feasible in PythonScript.
4. Contract logic stays **host-agnostic** in `shared/`; C++ only implements
   `CompactChrome`, `AnalyticPanel`, `ThemeBridge`.

Optional: PythonScript spike for clipboard bridge proof only (VP-NPP-0b).

---

## Three-host core strategy

```
shared/CHROME.md          ← surfaces + checklist (all hosts)
shared/chrome_contract    ← ACTION_KEYS, NESTS, grid_plan (VP-CH-5 Python)
shared/protocol           ← clipboard tokens
shared/res/               ← 16/24/32 glyphs

per host:
  CompactChrome           menu + toolbar adapter
  AnalyticPanel           side grid adapter
  ThemeBridge             editor tokens → RGB
```

**Cross-host tests:** export contract fixtures from Python `test_unit.py`; C++
and TS consume same JSON for `parse_show` / `grid_plan` parity.

**Risks:** three languages (Python / TS / C++) — mitigate with generated
contract + shared golden files; no hand-copy of `ACTION_KEYS`.

---

## SAP / CPR policy

| Artifact | Purpose |
|----------|---------|
| `plugins/notepadpp/w_todo/w_*/01_sap_notepadpp.txt` | Scope, surfaces, compromises, OUT |
| `plugins/notepadpp/w_todo/w_*/02_cpr_notepadpp.txt` | VP-NPP-* milestones |
| This file | Index + scorecard for all hosts |

Do **not** skip SAP/CPR — owner acronyms (SAP = policy, CPR = VP-* tracking)
already proved useful for CudaText and VS Code. Spike follows VP-NPP-0 GO.

---

## Related

- `plugins/cudatext/w_todo/w_en/03_sap_chrome.txt`
- `plugins/cudatext/w_todo/w_en/04_cpr_chrome.txt`
- `plugins/vscode/src/chromeContract.ts`, `panelProvider.ts`
- [N++ Plugin Communication](https://npp-user-manual.org/docs/plugin-communication/)
