plugins/ — one parent, one subfolder per host plugin
====================================================
Updated: 2026-08-24
Repo: jcfaria/statghost-plugins

Contract: this folder is the parent. Each client plugin is a
subfolder named after the host (no `STATghost-` prefix — the repo
already carries the brand). The student menu caption is always
**STATghost**.

What is general stays at the repo root (`shared/` including
`shared/png/`, `lexer/`, `lexer-dev/`, `docs/` for lexer sync).
What is specific to one host lives **inside that host folder**
(CODE, install, TF, chrome SAP/CPR).

  plugins/cudatext/    first host — CODE + its w_todo
  plugins/vscode/      VS Code / Cursor — GO+CODE (v0.1; see README.txt)
  plugins/notepadpp/   third host — GO+CODE (C++ DLL; see README.txt)

Do not put host plugins at the repo root.

Universal identity (menu / workbar / protocol): `../shared/README.txt`.
Tinn-R_D is a read-only peer, not a subfolder here.
