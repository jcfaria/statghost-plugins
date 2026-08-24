# STATghost Notepad++ plugin — lab (Windows)

VP-NPP-1 spike: Unicode C++ x64 DLL shell with STATghost menu commands and an
empty docked side panel (analytic keypad placeholder).

## Lab vs installed Notepad++ (read this first)

There are **two** Notepad++ trees on a typical Windows lab machine. The plugin
is installed into **one** of them — whichever `install_lab.ps1` could write to.

| Tree | Exe | Plugin path |
|------|-----|-------------|
| **Installed (winget)** | `C:\Program Files\Notepad++\notepad++.exe` | `C:\Program Files\Notepad++\plugins\STATghost\` |
| **Portable lab** | `plugins\notepadpp\.lab\notepad++.exe` | `plugins\notepadpp\.lab\plugins\STATghost\` |

If you open the **wrong** exe, **Plugins → STATghost** will not appear — the DLL
lives only in the other tree.

- **Program Files** needs admin/UAC to deploy (`install_lab.ps1` with
  `NPP_ROOT='C:\Program Files\Notepad++'`). Without elevation the script
  falls back to `.lab` automatically.
- After deploy, **restart** the same exe you use day-to-day (install kills any
  running `notepad++.exe`).
- Menu check: **Plugins → STATghost** (submenu with panel, clipboard probe, etc.).

Quick lab start (portable):

```powershell
Start-Process plugins\notepadpp\.lab\notepad++.exe
```

Install into Program Files (elevated):

```powershell
$env:NPP_ROOT = 'C:\Program Files\Notepad++'
$env:STATGHOST_NPP_SKIP_BUILD = '1'
powershell -File plugins\notepadpp\install_lab.ps1
# approve UAC if prompted
```

## Language choice (VP-NPP-1)

**C++ Unicode DLL** — matches SAP recommendation and official
`npp-plugins/plugintemplate`. Object Pascal (Lazarus/Delphi) is viable with the
same C ABI but has no official template; C++ was chosen for docking helpers
(`DockingDlgInterface`, `StaticDialog`) and future dark-mode work.

SDK headers are vendored under `statghost-npp/vendor/npp-sdk/` from
https://github.com/npp-plugins/plugintemplate (GPL-2; plugin sources are MIT-style
per repo; keep vendor NOTICE if redistributing).

## Prerequisites

- Notepad++ 8.5+ x64 (`C:\Program Files\Notepad++\notepad++.exe`)
- CMake 3.20+
- Visual Studio 2022 Build Tools — **Desktop development with C++** workload
  (`cl.exe`, Windows SDK, RC compiler)

## Build

From repo root or `plugins/notepadpp`:

```powershell
powershell -File plugins\notepadpp\build_lab.ps1
```

Manual steps:

```powershell
cd plugins\notepadpp\statghost-npp
cmake -S . -B build -A x64
cmake --build build --config Release
```

Output DLL: `plugins/notepadpp/statghost-npp/build/bin/STATghost/STATghost.dll`

## Deploy (lab)

```powershell
powershell -File plugins\notepadpp\install_lab.ps1
```

Default target order:

1. `$env:NPP_ROOT` if set
2. `C:\Program Files\Notepad++\` (winget install; deploy needs admin/UAC)
3. Portable lab tree `plugins/notepadpp/.lab/` (auto-created on first build if
   Program Files is not writable)

Copies/junctions:

- `STATghost.dll` → `<NPP_ROOT>\plugins\STATghost\`
- `shared/res/` → `<NPP_ROOT>\plugins\STATghost\res\shared\` (junction)

Portable lab exe: `plugins/notepadpp/.lab/notepad++.exe` (8.9.7 x64).

## Restart Notepad++

```powershell
powershell -File plugins\notepadpp\restart_lab.ps1
```

## Owner verification (VP-NPP-1)

1. **Plugins** menu → **STATghost** submenu with:
   - **Clipboard probe** — writes clipboard preview to status bar (typing mode).
   - **Show STATghost panel** — opens docked panel on the right.
2. Dock tab title: **STATghost**; client shows placeholder text.
3. Plugin loads without error on N++ 8.9+ x64.

D29: clipboard bridge only in this spike; no embedded R console.

## Related

- SAP: `plugins/notepadpp/w_todo/w_en/01_sap_notepadpp.txt`
- CPR: `plugins/notepadpp/w_todo/w_en/02_cpr_notepadpp.txt`
- Chrome contract: `shared/CHROME.md`
