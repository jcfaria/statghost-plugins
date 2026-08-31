STATghost plugin glyphs — canonical stash
=========================================

All chrome / brand / stash icons live here. Hosts copy this tree
(`cuda_statghost/res/`, `plugins/vscode/media/res/`). Do not add a
second icon set per editor.

Layout
------
  16px/ 24px/ 32px/     alpha masks (RGB black, shape in alpha)
  white/16px|24px|32px  closed white  #C4C4C4
  gray/16px|24px|32px   mid gray      #8A8A8A
  graphite/…            graphite      #3A3A3A

Rebuild after changing a source PNG (shared/png, shared/src/<stem>/{16,24,32}.png, Tinn stash, …):

  python shared/tools/build_res.py

Hosts
-----
CudaText toolbar/side: load mask + tint (icons.py). Pref icons.fg =
  auto | light (white) | dark (graphite) | gray | theme.
VS Code panel: same pref; CSS mask uses --sg-cell-fg.

Lab stash `plugins/cudatext/w_todo/icons/` stays as Tinn extract
reference. Production chrome does not load it.
