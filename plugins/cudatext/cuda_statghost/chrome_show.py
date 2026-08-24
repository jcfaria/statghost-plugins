# Shared toolbar / side-tab / Plugins-menu visibility (pure — no CudaText).
# Canonical contract: shared/CHROME.md (extract to shared/ on second host GO).
# One show-list, one nest tree, same action ids / same relative order.
# Menu, toolbar and side tab all use parent + children (NESTS).

from __future__ import annotations

# Canonical action ids — order matches chrome._TB (minus separators).
ACTION_KEYS = (
    'cfg', 'arm', 'host',
    'send', 'function', 'above', 'below', 'chunk',
    'source', 'srcsel', 'setwd',
    'inspect', 'ls', 'str', 'names', 'plot', 'help', 'head', 'tail',
    'clear', 'close_graphics', 'remove_objects', 'clear_all',
    'assign', 'pipe', 'outline',
)
# Classroom default: cores + Send/Source/Inspect/Clear extras (compacted
# on menu, toolbar and side tab via NESTS).
DEFAULT_SHOW = (
    'cfg', 'arm', 'host',
    'send', 'function', 'above', 'below', 'chunk',
    'source', 'srcsel', 'setwd',
    'inspect', 'ls', 'str', 'names', 'plot', 'help', 'head', 'tail',
    'clear', 'close_graphics', 'remove_objects', 'clear_all',
)

# Parent → related extras. Click = parent action; arrow / submenu = children.
NESTS = (
    ('send', ('function', 'above', 'below', 'chunk')),
    ('source', ('srcsel', 'setwd')),
    ('inspect', ('ls', 'str', 'names', 'plot', 'help', 'head', 'tail')),
    ('clear', ('close_graphics', 'remove_objects', 'clear_all')),
)

# Plugins menu + nest labels (same tree as the bars).
NEST_MENU = {
    'send': 'Send',
    'source': 'Source',
    'inspect': 'Inspect',
    'clear': 'Clear',
}
MENU_CAP = {
    'cfg': 'Config',
    'arm': 'Toggle Arm/Idle',
    'host': 'Start/Quit STATghost',
    'send': 'Send',
    'function': 'Function',
    'above': 'Above',
    'below': 'Below',
    'chunk': 'Chunk',
    'source': 'Source',
    'srcsel': 'Src sel',
    'setwd': 'setwd',
    'inspect': 'Print',
    'ls': 'ls()',
    'str': 'str()',
    'names': 'names()',
    'plot': 'plot()',
    'help': 'Help',
    'head': 'head()',
    'tail': 'tail()',
    'clear': 'Clear',
    'close_graphics': 'graphics.off',
    'remove_objects': 'rm all',
    'clear_all': 'Clear all',
    'assign': 'Insert <-',
    'pipe': 'Insert pipe',
    'outline': 'Outline…',
}
ACTION_METHODS = {
    'cfg': 'config',
    'arm': 'toggle_arm',
    'host': 'toggle_host',
    'send': 'send_selection',
    'function': 'send_function',
    'above': 'send_above',
    'below': 'send_below',
    'chunk': 'send_chunk',
    'source': 'send_file',
    'srcsel': 'source_selection',
    'setwd': 'set_wd_here',
    'inspect': 'inspect_print',
    'ls': 'inspect_ls',
    'str': 'inspect_str',
    'names': 'inspect_names',
    'plot': 'inspect_plot',
    'help': 'inspect_help',
    'head': 'inspect_head',
    'tail': 'inspect_tail',
    'clear': 'clear_console',
    'close_graphics': 'inspect_graphics_off',
    'remove_objects': 'inspect_rm_all',
    'clear_all': 'inspect_clear_all',
    'assign': 'insert_assign',
    'pipe': 'insert_pipe',
    'outline': 'show_outline',
}


def nest_parent(key):
    """Parent action id if *key* is a nest child; else None."""
    for parent, kids in NESTS:
        if key in kids:
            return parent
    return None


def menu_path(key):
    """Caption after `STATghost\\` — submenu for nests, else top-level."""
    cap = MENU_CAP.get(key, key)
    if key in NEST_MENU:
        return NEST_MENU[key] + '\\' + cap
    parent = nest_parent(key)
    if parent:
        return NEST_MENU[parent] + '\\' + cap
    return cap


def collapse_keys(keys):
    """Drop children whose parent is also present (toolbar / side / menu)."""
    present = []
    seen = set()
    for key in keys:
        if key in ACTION_KEYS and key not in seen:
            present.append(key)
            seen.add(key)
    hide = set()
    have = set(present)
    for parent, kids in NESTS:
        if parent in have:
            hide.update(k for k in kids if k in have)
    return tuple(k for k in present if k not in hide)

# Command methods `-p=cuda_statghost#method` may invoke (lab / cyclic TF).
# Config / Arm / Start-Quit stay human clicks — TDR + session safety.
CLI_METHODS = frozenset((
    'send_selection', 'send_function', 'send_above', 'send_below', 'send_chunk',
    'send_file', 'source_selection', 'set_wd_here',
    'inspect_print', 'inspect_ls', 'inspect_str', 'inspect_names',
    'inspect_plot', 'inspect_help', 'inspect_head', 'inspect_tail',
    'inspect_graphics_off', 'inspect_rm_all', 'inspect_clear_all',
    'clear_console',
))
# Gentle cyclic live EVAL — no plot/help windows, no rm, no Config.
CYCLE_METHODS = frozenset((
    'send_selection', 'inspect_ls', 'inspect_print', 'inspect_str',
    'inspect_names', 'inspect_head', 'inspect_tail', 'inspect_graphics_off',
    'set_wd_here', 'clear_console',
))


def encode_checklist(show_on, keys):
    """dlg_proc / dlg_custom checklistbox val: `index;0,1,0,…`."""
    bits = ['1' if show_on.get(k) else '0' for k in keys]
    return '0;' + ','.join(bits)


def decode_checklist(raw, keys, fallback=None):
    """Parse checklistbox val back to {key: bool}."""
    s = str(raw if raw is not None else '').strip()
    if ';' in s:
        s = s.split(';', 1)[-1]
    parts = [p.strip() for p in s.split(',')]
    if len(parts) < len(keys):
        if fallback is not None:
            return dict(fallback)
        return {k: False for k in keys}
    out = {}
    for i, k in enumerate(keys):
        out[k] = parts[i] in ('1', 'true', 'yes', 'on')
    return out


_GROUP_HOST = frozenset(('cfg', 'arm', 'host'))
_GROUP_SEND = frozenset((
    'send', 'function', 'above', 'below', 'chunk',
    'source', 'srcsel', 'setwd',
    'inspect', 'ls', 'str', 'names', 'plot', 'help', 'head', 'tail',
    'clear', 'close_graphics', 'remove_objects', 'clear_all',
))
_GROUP_EDIT = frozenset(('assign', 'pipe', 'outline'))
_GROUPS = (_GROUP_HOST, _GROUP_SEND, _GROUP_EDIT)


def parse_show(raw, default=None):
    """Parse CSV / whitespace list → ordered tuple of known action keys."""
    if default is None:
        default = DEFAULT_SHOW
    if raw is None:
        return tuple(default)
    text = str(raw).strip()
    if text == '':
        return tuple(default)
    parts = []
    for chunk in text.replace(';', ',').replace(' ', ',').split(','):
        key = chunk.strip().lower()
        if key in ACTION_KEYS and key not in parts:
            parts.append(key)
    if not parts:
        return tuple(default)
    return tuple(k for k in ACTION_KEYS if k in parts)


def format_show(keys):
    """CSV for ini — only known keys, canonical order."""
    return ','.join(parse_show(','.join(keys or ()), default=()))


def nest_children(parent):
    """Related extras for a parent button (empty if none)."""
    for name, kids in NESTS:
        if name == parent:
            return kids
    return ()


def nest_menu_keys(parent, show_keys):
    """Children of *parent* that are currently shown (menu contents)."""
    if show_keys is None:
        show = set(DEFAULT_SHOW)
    else:
        keys = tuple(show_keys)
        if not keys:
            return ()
        show = set(parse_show(','.join(keys), default=()))
    return tuple(k for k in nest_children(parent) if k in show)


def collapse_nested_rows(tb_rows):
    """Drop child buttons whose parent is already on the bar.

    Separators with no remaining neighbours are left for the caller;
    filter_toolbar_rows already places seps between groups.
    """
    present = {row[0] for row in tb_rows if row[2] is not None}
    hide = set()
    for parent, kids in NESTS:
        if parent in present:
            hide.update(k for k in kids if k in present)
    if not hide:
        return tuple(tb_rows)
    return tuple(row for row in tb_rows if row[0] not in hide)


def filter_toolbar_rows(tb_rows, show_keys):
    """Filter _TB-like rows: leading sep + visibles + mid seps between groups.

    tb_rows: iterable of (name, hint, method, icon); method is None for seps.
    show_keys: iterable of action ids. Explicit empty → no buttons.
    Does **not** collapse nests — call collapse_nested_rows (toolbar)
    or filter_side_actions (side tab) so all three surfaces share NESTS.
    """
    if show_keys is None:
        show = set(DEFAULT_SHOW)
    else:
        keys = tuple(show_keys)
        if not keys:
            return ()
        show = set(parse_show(','.join(keys), default=()))
        if not show:
            return ()
    actions = [
        row for row in tb_rows
        if row[2] is not None and row[0] in show
    ]
    if not actions:
        return ()
    buckets = []
    for group in _GROUPS:
        part = [r for r in actions if r[0] in group]
        if part:
            buckets.append(part)
    out = []
    if tb_rows and tb_rows[0][2] is None:
        out.append(tb_rows[0])
    seps = [row for row in tb_rows if row[2] is None]
    mid_seps = seps[1:] if len(seps) > 1 else []
    for i, part in enumerate(buckets):
        if i > 0:
            if i - 1 < len(mid_seps):
                out.append(mid_seps[i - 1])
            else:
                out.append(('sep_%d' % i, '-', None, None))
        out.extend(part)
    return tuple(out)


def filter_side_actions(side_rows, show_keys):
    """Filter side rows — same nest collapse as the main toolbar."""
    if show_keys is None:
        show = set(DEFAULT_SHOW)
    else:
        keys = tuple(show_keys)
        if not keys:
            return ()
        show = set(parse_show(','.join(keys), default=()))
    rows = tuple(row for row in side_rows if row[0] in show)
    keep = set(collapse_keys(tuple(r[0] for r in rows)))
    return tuple(row for row in rows if row[0] in keep)


def side_keys(show_keys=None):
    """Collapsed toolbar ids for the current chrome.show set."""
    if show_keys is None:
        wanted = set(DEFAULT_SHOW)
    else:
        keys = tuple(show_keys)
        if not keys:
            return ()
        wanted = set(parse_show(','.join(keys), default=()))
    return collapse_keys(tuple(k for k in ACTION_KEYS if k in wanted))


GRID_COLS = 3


# Analytic side grid: one button per action, grouped by nest families.
GRID_GROUPS = (
    ('cfg', 'arm', 'host'),
    ('send', 'function', 'above', 'below', 'chunk'),
    ('source', 'srcsel', 'setwd'),
    ('inspect', 'ls', 'str', 'names', 'plot', 'help', 'head', 'tail'),
    ('clear', 'close_graphics', 'remove_objects', 'clear_all'),
    ('assign', 'pipe', 'outline'),
)
GRID_GROUP_TITLES = (
    'Host', 'Send', 'Source', 'Inspect', 'Clear', 'Edit',
)
# Short keypad captions — equal cells; full hint stays on the button.
GRID_CAP = {
    'cfg': 'Config',
    'arm': 'Idle',
    'host': 'Start',
    'send': 'Send',
    'function': 'Func',
    'above': 'Above',
    'below': 'Below',
    'chunk': 'Chunk',
    'source': 'Source',
    'srcsel': 'Sel',
    'setwd': 'setwd',
    'inspect': 'Print',
    'ls': 'ls',
    'str': 'str',
    'names': 'names',
    'plot': 'plot',
    'help': 'help',
    'head': 'head',
    'tail': 'tail',
    'clear': 'Clear',
    'close_graphics': 'g.off',
    'remove_objects': 'rm',
    'clear_all': 'all',
    'assign': '<-',
    'pipe': 'pipe',
    'outline': 'out',
}


# Keypad cell min-width: longest GRID_CAP × em × slack.
# Same 20% rule as Config nav (_TREE_SLACK). Keypad font is ~9px so
# GRID_EMU_CHAR is 7 (Config tree uses 8).
GRID_CAP_SLACK = 1.20
GRID_EMU_CHAR = 7
GRID_CELL_MIN = 36  # icon-tier floor; below mode grows with captions


def grid_cell_w(caps=None):
    """Min keypad cell width from the longest caption + 20%.

    Dynamic: a longer GRID_CAP (or a test override) widens every cell
    so neighbours like Source|Sel stay distinct without a fixed px guess.
    """
    vals = caps if caps is not None else GRID_CAP.values()
    n = max((len(str(c)) for c in vals), default=1)
    return max(GRID_CELL_MIN, int(round(n * GRID_EMU_CHAR * GRID_CAP_SLACK)))


# Horizontal slack on the side keypad — mirrors chrome._grid_bind_row /
# grid sp_l/sp_r. Used by grid_panel_min_w_formula() for reference only.
GRID_ROW_EDGE = 4       # outer cell sp_l / sp_r
GRID_ROW_GUTTER = 3     # between adjacent cells (sp_r + sp_l)
GRID_SCROLL_PAD = 4     # grid panel sp_l + sp_r (2 + 2)

# Owner lab minimum — CudaText-jcf history.json size_side and
# default.cuda-session panels.side_size (2026-08-23). Locked: do not
# derive from grid_cell_w() alone (formula ~174 understates usability
# at the owner's chosen splitter width of 150 px).
GRID_PANEL_MIN_W = 150


def grid_panel_min_w_formula(cell_w=None, cols=GRID_COLS):
    """Caption-based keypad width (reference / tests). Not the live floor."""
    cw = cell_w if cell_w is not None else grid_cell_w()
    inner = max(0, cols - 1) * (GRID_ROW_GUTTER + GRID_ROW_GUTTER)
    return cols * cw + GRID_ROW_EDGE + GRID_ROW_EDGE + inner + GRID_SCROLL_PAD


def grid_panel_min_w(cell_w=None, cols=GRID_COLS):
    """Min STATghost side-tab width (px).

    Default GRID_PANEL_MIN_W (150). Optional raise-only override:
    cuda_statghost.ini [chrome] grid_panel_min_w=NNN.
    """
    w = GRID_PANEL_MIN_W
    try:
        try:
            from . import prefs
        except ImportError:
            import prefs
        ow = prefs.get_grid_panel_min_w()
        if ow is not None and ow > w:
            w = int(ow)
    except Exception:
        pass
    return w


# Side keypad captions: default below = names without widening the deck.
# icon = glyphs only (hover hint).
GRID_LABEL_DEFAULT = 'below'
GRID_LABELS = ('below', 'icon')


def parse_grid_label(raw):
    """Clamp chrome.grid_label — empty / junk → below."""
    key = (raw or '').strip().lower()
    aliases = {
        'under': 'below',
        'vert': 'below',
        'vertical': 'below',
        'only': 'icon',
        'icons': 'icon',
        'horz': 'icon',
        'horiz': 'icon',
        'side': 'icon',
        'beside': 'icon',
    }
    key = aliases.get(key, key)
    if key in GRID_LABELS:
        return key
    return GRID_LABEL_DEFAULT


def grid_keys():
    """Every plugin action — analytic deck does not collapse nests."""
    return ACTION_KEYS


def grid_plan(keys=None, cols=GRID_COLS):
    """Hierarchical rows for the side-tab analytic keypad.

    ('hdr', title) then ('row', (key, …)) per GRID_GROUPS family.
    """
    if cols < 1:
        cols = GRID_COLS
    if keys is None:
        wanted = set(ACTION_KEYS)
    else:
        wanted = {k for k in ACTION_KEYS if k in set(keys)}
    plan = []
    for title, group in zip(GRID_GROUP_TITLES, GRID_GROUPS):
        part = tuple(k for k in group if k in wanted)
        if not part:
            continue
        plan.append(('hdr', title))
        for i in range(0, len(part), cols):
            plan.append(('row', part[i:i + cols]))
    return tuple(plan)
