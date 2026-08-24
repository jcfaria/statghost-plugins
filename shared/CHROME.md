# STATghost Chrome Pattern

**Multi-editor contract** for how STATghost actions appear in every host:
one action registry, three surfaces, theme-derived visuals. The student sees
the same **STATghost** identity whether the host is CudaText, VS Code, or
another editor.

Canonical implementation today:

| Host | Module |
|------|--------|
| CudaText (first) | `plugins/cudatext/cuda_statghost/chrome_show.py` |
| VS Code / Cursor | `plugins/vscode/src/chromeContract.ts` (TS port, keep in sync) |

Extract host-agnostic **Python** into `shared/` when both hosts are stable
(VP-CH-5) — do not copy-paste. The TypeScript port is the VS Code source of
truth until a shared package exists.

---

## 1. One contract, three surfaces

The same `action_id`, relative order, and `NESTS` tree drive every surface.
Only the host widgets differ.

| Surface | Behaviour |
|---------|-----------|
| **Menu / toolbar** | Synthetic nests — Send▾, Source▾, Inspect▾, Clear▾. Parent click = primary action; arrow = children. Toolbar **collapses** children while the parent is visible. |
| **Side panel** | Analytic grid — family bands (Host, Send, Source, …) plus **one button per visible action**. Nests are **never** collapsed; every shown key gets its own cell. |
| **Config** | Tree by domain (Send / Chrome / Host). `chrome.show` checklist filters the same key set on all surfaces. |

Menu, compact bar, and side tab must stay in sync: same keys, same order,
same nest semantics.

---

## 2. Canonical action registry

Each action is **one registry entry**. Fields (today in `chrome_show.py`):

```
action_id → method → hint → icon → family → GRID_CAP → menu_path
```

**Add a new action** in this order:

1. Append to `ACTION_KEYS` (canonical order).
2. If nested, add the child under `NESTS` and `NEST_MENU`.
3. Fill `ACTION_METHODS`, `MENU_CAP`, icon map, `GRID_GROUPS`, `GRID_CAP`.
4. Opt in via `DEFAULT_SHOW` or require explicit `chrome.show`.
5. Run unit tests (`grid_plan`, `parse_show`, collapse rules).

**Flow:** `ACTION_KEYS` → `NESTS` (if child) → `GRID_GROUPS` / `GRID_CAP` →
`DEFAULT_SHOW` or `chrome.show` opt-in.

The analytic panel uses `grid_plan()` — it never collapses nests.

---

## 3. Visual language

Derived from CudaText lab TF; hosts should match the intent, not pixel-copy
Win32.

**Family bands**

- Background from theme tokens (`_hdr_band_bg` — TabBg, ButtonBgPassive, …).
- Label: TabFont, **bold uppercase** (HOST, SEND, SOURCE, …).
- No icons in the band header.

**Action cells**

- Icon + short `GRID_CAP` label (equal-width grid cells).
- Caption contrast via `icons_fg` / `pick_fg_rgb('auto')` — not bold.
- Full hint on hover.
- Semantic colour **only** for arm / host state icons (armed vs idle, SG
  running vs stopped). All other glyphs follow the neutral tint pipeline.

**Side grid layout**

- Default three columns (`GRID_COLS = 3`); `grid_cols` pref reserved for
  future host support.
- `grid_label`: `below` (default) | `icon`.

---

## 4. Theme = automatic

- Backgrounds and band colours come from editor theme tokens (TabBg,
  ButtonBgPassive, TabFont, ButtonFont, …).
- Glyphs and captions use `pick_fg_rgb(auto)` against the cell background.
- No hardcoded lab greys except fallback when tokens collapse to the same
  RGB.
- Must work light/dark and gtk2/Win32 (CudaText reference host).

Prefs: `icons_fg` = `auto` | `light` | `dark` | `theme`.

---

## 5. Extract to `shared/` (second host GO)

**2026-08-22:** VS Code host has GO+CODE (`plugins/vscode/`). TypeScript
contract ports live beside the extension; CudaText still uses
`chrome_show.py`. Python extract to `shared/` (VP-CH-5) waits until both
hosts share tests / import path without breakage.

Keep host-agnostic contract beside each host until replication is proven.
Then move Python without behaviour change:

| Module | Contents |
|--------|----------|
| `chrome_contract` | `ACTION_KEYS`, `NESTS`, `GRID_*`, `grid_plan`, `parse_show`, collapse helpers |
| `icons_fg` | `pick_fg_rgb`, contrast helpers |
| `protocol` | Clipboard `#. STATGHOST:<CMD>` tokens |
| `rword` | Identifier under caret (Inspect family) |

**Per host:** `CompactChrome` (menu/toolbar nests), `AnalyticPanel` (side
grid), `ThemeBridge` (token → RGB adapters).

Glyphs: canonical stash `shared/png/`; each host ships a loadable subset
beside its CODE (CudaText: `plugins/cudatext/cuda_statghost/png/`).

---

## 6. Config preferences

| Key | Purpose |
|-----|---------|
| `chrome.show` | Comma-separated action ids (or checklist in Config UI). Filters menu, toolbar, and side grid. |
| `grid_label` | Side cell layout: `below` / `icon`. |
| `icons_fg` | Glyph/caption contrast: `auto` / `light` / `dark` / `theme`. |
| `grid_cols` | Reserved — column count for analytic grid (default 3). |

---

## 7. New host checklist

Before calling a host “STATghost-ready”:

- [ ] Plugins menu group **STATghost** (not host-branded).
- [ ] Compact bar with synthetic nests (Send▾ / Source▾ / Inspect▾ / Clear▾).
- [ ] Side analytic panel: family bands + full action grid (no nest collapse).
- [ ] Config page: `chrome.show` checklist aligned with domains.
- [ ] Icons from `shared/png/` subset; same action ids as `ACTION_KEYS`.
- [ ] Unit tests for registry, `parse_show`, `grid_plan`, nest collapse.
- [ ] TF: light and dark theme screenshots of bar + side panel.

---

## Related docs

- `shared/README.txt` — repo-wide identity and D29 boundary.
- `plugins/cudatext/w_todo/w_en/03_sap_chrome.txt` — SAP (CudaText host).
- `plugins/cudatext/w_todo/w_en/04_cpr_chrome.txt` — CPR / VP-CH-* tracking.
- `shared/NOTEPADPP.md` — Notepad++ host (GO+CODE lab; VP-NPP-*).
- `plugins/notepadpp/w_todo/` — N++ SAP/CPR packs (01/02, EN ↔ PT).
- `.cursor/rules/sidebar-panel.mdc` — CudaText side-tab implementation rule.

**Policy:** one STATghost, many hosts. Never embed Console / Plot / Explorer
in the client (D29).
