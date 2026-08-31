# STATghost-plugins — News

Peer plugins and canonical lexers for
[STATghost](https://github.com/jcfaria/statghost). One repo, one menu
identity (**STATghost**), multiple editor hosts under `plugins/`. App-side
bridge, Explorer, Console, and packaged releases are recorded in the
[sibling News](https://github.com/jcfaria/statghost/blob/work/news/News.md).

---

## Unreleased — 2026-08-31 - Faria, J. C.

_(nothing yet)_

## 2026-08-31 — Icon res rebuild

- **Regenerated host `res/` trees** from `shared/tools/build_res.py` after
  lab rebuild (CudaText, VS Code media, Notepad++ when present, plus
  `shared/res/`). All variant folders (default, gray, graphite, white) at
  16/24/32 px — keeps multi-host chrome glyphs in sync with `shared/png`
  and `shared/src/<stem>/`.

## 2026-08-30 — News mirror

- **News mirror (this repo).** `news/News.md` + `news.html` + `news.css`
  (charcoal / ghost-slate theme, same tokens as STATghost and statghost-ext).
  Regenerate with `./news/sync_news.sh`. `docs/News.md` pointer; README link.
  Peer history backfilled from git log + sibling News (plugin bullets only).

## 2026-08-23 — Multi-host chrome v0.1

- **Outline (side tab).** Jump accepts `dlg_proc` args; click and double-click
  wired so the side-tab Outline opens the correct target.
- **Bridge state poll.** Plugin reads STATghost `bridge_state.json` and
  rebinds Qt6 glyphs so Arm/Idle and Start/Quit paint correctly after host
  theme or bridge changes.
- **Notepad++ host.** Consolidated under `plugins/notepadpp/` with Explorer
  Print glyphs aligned to shared chrome.
- **Multi-host chrome v0.1.** VS Code / Cursor extension (`plugins/vscode/`),
  shared icon pipeline (`shared/tools/build_res.py`), Notepad++ stub, one
  nest tree across menu · toolbar · side tab.

## 2026-08-17 — Config tree, Send focus, functional TF

- **Config (CudaText):** tree pages **Send** / **Chrome** / **Host** replace
  one stacked dialog. Send hint and Host paths use memo wrap instead of
  clipping (“Sniper” label, long exe paths).
- **EVAL_KEEP:** after Send, editor keeps focus (no steal back to STATghost).
- **Functional TF:** wait for ARM to settle before the first live EVAL.

## 2026-08-16 — Multi-host layout + WORKBAR

- **Rename `statghost-cudatext` → `statghost-plugins`.** Host plugins under
  `plugins/`; shared glyphs in `shared/png/`. Build/pack looks for
  `statghost-plugins/lexer` first, then the old folder name.
- **Sibling STATghost discovery:** walk up to the sibling clone instead of
  hardcoding folder depth.
- **WORKBAR (Tinn-R_D TBRMain analogue):** nested Send/Source/Inspect/Clear
  on toolbar; Tinn R-control glyphs; live Send on Linux (not only Win32);
  Win10 `sibling_dir` reunified with Linux workbar Send.
- **Production TF:** CudaText Send into a running STATghost (clipboard
  contract); hardened tab-title wait; no Python eval / orphan `with(BOD)` in R
  path.

## 2026-08-15 — Public companion, Send advance, collapse

- **Repo public** with install docs and MPL-2.0 footer (Author/Maintainer
  aligned with STATghost README).
- **Send advance (golden rule):** after successful Send, caret moves to column
  0 of the next executable line; skip blank and `#` comment-only lines; stay
  at EOF (no wrap). Reference: `editor.py` / `editor.ts`.
- **Send payload:** non-empty selection → selection; empty → enclosing
  function or complete R statement at caret (`statement.py`).
- **Collapse:** bracket-aware wrap for Console one-liners; `{ }` blocks keep
  newlines (no glue inside `with(BOD, { … })`). Python `try`/`def`/`"""` units
  locked with sample tests.
- **Live functional tests** for clipboard send contract.

## 2026-08-14 — VP-EB-1b chrome (CudaText)

Mirrors [STATghost v0.4.26 News](https://github.com/jcfaria/statghost/blob/work/news/News.md)
(plugin bullets); highlights for this repo:

- **Bridge (VP-EB-1 / EB-1b):** native toolbar + side tab (Config · Arm/Idle ·
  Start/Quit · Send · Source · Clear). Side-tab order = toolbar order.
- **Source via `.paths[4]`:** writes `TEMP/STATghost/file.R`, sends
  `source(.paths[4], …)` — no absolute editor path (STATghostcom 0.0.12).
- **Config:** chrome visibility checkboxes (+ All/None); Insert pipe `|>` /
  `%>%`; Outline; Send above/below; Source selection; enclosing function;
  didactic hotkeys; icon FG contrast (`auto` / light / dark / theme).
- **Start/Quit:** recovers windowless D50 zombies; Quit force-stops after 3s.
- **Unit tests:** collapse, protocol, `.paths`, workbar nests.

## 2026-08-13 — VP-EB-1 bootstrap

- **First CudaText plugin:** clipboard Send to Armed STATghost (`#. STATGHOST:EVAL`).
- **Absolute Arm/Idle tokens** (never guessed toggle from chrome).
- **Complete R statement** at caret, including unbraced `if` bodies.
- **Drop default Ctrl+E** from plugin hotkeys (Send uses install.inf chords).

---

## Hosts (current)

| Host | Path | Notes |
|------|------|-------|
| CudaText | `plugins/cudatext/cuda_statghost/` | Primary lab; gtk2 + Qt6; WORKBAR SAP |
| VS Code / Cursor | `plugins/vscode/` | Extension v0.1; panel, submenus, bridge |
| Notepad++ | `plugins/notepadpp/` | v1 stub; Send advance mandatory |

Shared contract: `shared/` (menu, workbar, protocol, glyphs). Lexers:
`lexer-dev/` → promoted `lexer/`.

---

## Glossary

- **AN** — advance notice (changelog intent before CP).
- **CP / CPMW** — commit+push (MW = multi-worktree / companion repos).
- **D29** — SAP/CPR: STATghost owns REPL+Explorer; plugins are peers only.
- **EVAL_KEEP** — keep editor focused after Send (Config / bridge).
- **VP-EB-1** — editor bridge pack 1 (CudaText control deck).
- **WORKBAR** — nested toolbar analogue to Tinn-R_D TBRMain (`w_todo` VP-WB-*).

---

## See also

- [STATghost News](https://github.com/jcfaria/statghost/blob/work/news/News.md) —
  app releases, Explorer, Console, bridge_state, packaged zips.
- [statghost-ext News](https://github.com/jcfaria/statghost-ext/blob/main/News.md) —
  STATghostcom / `.paths` detail.
- Browser mirror: open `news/news.html` locally (stylesheet `news.css`).
