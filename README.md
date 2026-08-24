# STATghost-plugins

Public companion to **[STATghost](https://github.com/jcfaria/statghost)** —
peer plugins and canonical lexers. One identity for the student
(**STATghost** in the client: menu + unified workbar + clipboard contract).
Each editor is a host folder, not a separate product.

**Repo:** https://github.com/jcfaria/statghost-plugins  
Formerly `statghost-cudatext` (GitHub keeps a redirect).

STATghost remains the sniper matchbox. This repo owns **peer** artefacts —
not a REPL+Explorer bundle (D29).

## Layout

| Path | Role |
|------|------|
| `shared/` | Universal contract (menu, workbar, protocol, glyphs) |
| `shared/png/` | Same chrome/brand glyphs for every host |
| `plugins/` | Parent folder — one subfolder per host plugin |
| `plugins/cudatext/` | CudaText host (CODE, install, TF, workbar SAP) |
| `plugins/vscode/` | VS Code / Cursor host — extension v0.1 (panel, submenus, bridge) |
| `lexer-dev/` | Workshop LCF packs |
| `lexer/` | Promoted packs (CudaText `data/lexlib` + STATghost Console via build) |
| `docs/` | Notes + optional sync into STATghost `_out/lexer` |

The folder name on disk is the host; the menu caption is always
**STATghost**. Hosts today: CudaText, VS Code / Cursor, Notepad++ (`plugins/notepadpp/`).

## CudaText (lab)

STATghost must be **running**. **Toggle Arm/Idle** sends an absolute
`#. STATGHOST:ARM` or `#. STATGHOST:IDLE` token (never `TOGGLE_ARM` from
the button — a guessed flip desyncs the plugin chrome). Send of code
uses `#. STATGHOST:EVAL <nonce>` plus the student chunk, so the same
selection can be re-sent (pseudo-random reruns).
Eval still requires Armed. Empty selection → complete **statement** at the
caret (brackets, trailing operators, and unbraced R `if (cond)` plus
its multi-line body — RStudio Ctrl+Enter idea). After a successful
send, the caret advances to the next code line and **stops**.

Menu, toolbar and side tab share **one nest tree**: parent click = action,
arrow / submenu = children (`Send▾` `Source▾` `Inspect▾` `Clear▾`).
Config (tree **Send** / **Chrome** / **Host**) no longer stacks everything
in one 560px pane.

**Linux** (portable sibling + `cuda_jcf/run.sh`):

```bash
bash plugins/cudatext/install_lab.sh
# or: CUDA_ROOT=/path/to/CudaText bash plugins/cudatext/install_lab.sh
```

**Windows 11 dev** (always **CudaText-jcf**, not upstream `CudaText/`):

```powershell
powershell -File plugins/cudatext/install_lab.ps1
# default: ~/Documents/Github/CudaText-jcf/app/bin/windows-amd64/py/cuda_statghost
```

Restart CudaText after plugin changes (Python is cached until restart). Then:

- **Plugins → STATghost → Send → Send** (selection / statement)
- **Plugins → STATghost → Source / Inspect / Clear** (same children as the bars)
- **Plugins → STATghost → Toggle Arm/Idle**
- **Plugins → STATghost → Start/Quit STATghost**
- First-install chords in `install.inf` (`Ctrl+Enter` Send, …); extra
  binds in Command Palette → **F9**

Engine = whatever STATghost has Armed (R / Python / Julia). Same chunk
sent twice without a clipboard change is skipped (same as a human Copy).

Do **not** embed a REPL inside CudaText.

TF: `bash plugins/cudatext/run_tf.sh` (unit + functional + production).
Workbar: `STATGHOST_WORKBAR_TF=cuda|full python3 plugins/cudatext/cuda_statghost/test_workbar.py`
(Linux live Send uses the same X11 path as production — `/tmp/sg_prod_venv`).

## Relationship

```
statghost-plugins/lexer   ← canonical packs
        │
        ├─→ CudaText data/lexlib
        └─→ STATghost src/build.ps1 → src/_out/lexer/

statghost-plugins/plugins/cudatext/cuda_statghost
        ├─→ CudaText-jcf app/bin/windows-amd64/py/cuda_statghost  (install_lab.ps1)
        └─→ portable app/py/cuda_statghost  (install_lab.sh + CUDA_ROOT)
```

STATghost source keeps **only** `lexer/README.txt` (no LCF duplicates;
no Pascal for EB-1 v1). Motto: Keep this project as simple and effective as possible.

---

## Author / Maintainer

Started and maintained by:

**Faria, J. C.**  
Universidade Estadual de Santa Cruz — UESC  
Departamento de Ciências Exatas — DCEX  
Ilhéus — Bahia — Brazil

---

## License

**Mozilla Public License 2.0 (MPL-2.0)** — see [`LICENSE`](LICENSE).
