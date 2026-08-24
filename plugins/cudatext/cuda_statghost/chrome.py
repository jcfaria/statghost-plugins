# Native CudaText chrome (VP-EB-1b).
# Toolbar + side *control deck* (mission §5): send and host commands
# stay in the editor so the classroom does not bounce to STATghost.
# Never embed Console / Plot / Explorer.

from __future__ import annotations

import os

from cudatext import ALIGN_BOTTOM
from cudatext import ALIGN_CLIENT
from cudatext import ALIGN_NONE
from cudatext import ALIGN_TOP
from cudatext import BTN_GET_DATA2
from cudatext import BTN_SET_DATA1
from cudatext import BTN_SET_DATA2
from cudatext import BTN_SET_ENABLED
from cudatext import BTN_SET_HINT
from cudatext import BTN_SET_IMAGEINDEX
from cudatext import BTN_SET_IMAGELIST
from cudatext import BTN_SET_ARROW
from cudatext import BTN_SET_BOLD
from cudatext import BTN_SET_KIND
from cudatext import BTN_SET_MENU
from cudatext import BTN_SET_TEXT
from cudatext import BTN_SET_VISIBLE
from cudatext import BTN_SET_WIDTH
from cudatext import BTNKIND_ICON_ONLY
from cudatext import BTNKIND_SEP_HORZ
from cudatext import BTNKIND_SEP_VERT
from cudatext import DLG_CREATE
from cudatext import DLG_CTL_ADD
from cudatext import DLG_CTL_DELETE
from cudatext import DLG_CTL_HANDLE
from cudatext import DLG_CTL_PROP_GET
from cudatext import DLG_CTL_PROP_SET
from cudatext import DLG_LOCK
from cudatext import DLG_PROP_SET
from cudatext import DLG_UNLOCK
from cudatext import IMAGELIST_ADD
from cudatext import IMAGELIST_CREATE
from cudatext import IMAGELIST_DELETE_ALL
from cudatext import IMAGELIST_GET_SIZE
from cudatext import IMAGELIST_SET_SIZE
from cudatext import MENU_ADD
from cudatext import MENU_CREATE
from cudatext import MENU_ENUM
from cudatext import MENU_REMOVE
from cudatext import PROC_GET_MAIN_TOOLBAR
from cudatext import PROC_SHOW_SIDEPANEL_SET
from cudatext import PROC_SIDEPANEL_ACTIVATE
from cudatext import PROC_SIDEPANEL_ADD_DIALOG
from cudatext import PROC_THEME_UI_DICT_GET
from cudatext import TIMER_START
from cudatext import TOOLBAR_ADD_ITEM
from cudatext import TOOLBAR_DELETE_BUTTON
from cudatext import TOOLBAR_GET_BUTTON_HANDLE
from cudatext import TOOLBAR_GET_COUNT
from cudatext import TOOLBAR_GET_IMAGELIST
from cudatext import TOOLBAR_SET_WRAP
from cudatext import TOOLBAR_SET_VERTICAL
from cudatext import TOOLBAR_THEME
from cudatext import TOOLBAR_UPDATE
from cudatext import app_proc
from cudatext import button_proc
from cudatext import dlg_proc
from cudatext import imagelist_proc
from cudatext import menu_proc
from cudatext import msg_status
from cudatext import timer_proc
from cudatext import toolbar_proc

try:
    from . import chrome_show
    from . import host
    from . import icons as icontint
    from . import outline as sgoutline
    from . import prefs
except ImportError:
    import chrome_show
    import host
    import icons as icontint
    import outline as sgoutline
    import prefs

PLUGIN = 'STATghost'
TITLE = 'STATghost'
TAG = 'statghost-eb1'
TOOLS_CAP = 'Tools'
TICK_MS = 2000
GRID_ROW_H = 32
GRID_HDR_H = 18
GRID_RULE_H = 1
GRID_CELL_W = 88
GRID_CAP_H = 17
# Side imagelist is 16px. The below-mode toolbar used to eat the leftover
# of row_h − GRID_CAP_H (35px in a 52px row), so LCL centered the glyph
# and left ~10px of air above the caption. Hug the icon instead.
GRID_ICON_STRIP_H = 20
# Narrow + dense: button count will grow. icon = tight glyphs; below =
# icon strip + caption label (contrast via icons_fg, not ButtonFont).
_GRID_METRICS = {
    'icon': (26, 20),
    'below': (36, GRID_ICON_STRIP_H + GRID_CAP_H),
}
STATUS_H_MAX = 96
STATUS_LINE_H = 18

# name, hint, Command method, icon file (or None = separator).
# Order: sep | SG chrome (Settings, Arm, Kill) | sep | editor Send/Clear.
# Same left-to-right as FormMain (Settings → Arm → Kill). Panel /
# Explorer / OnTop stay in STATghost. Clear Console is here (owner).
#
# GOLDEN RULE — same action ids / same relative order / same nests on
# Plugins menu, toolbar and side tab. Parent click = action; arrow /
# submenu = children (Send / Source / Inspect / Clear).
_TB = (
    ('sep', '-', None, None),
    ('cfg', 'STATghost plugin Config', 'config', 'setting-lines.png'),
    ('arm', 'Toggle Arm/Idle', 'toggle_arm', 'idle.png'),
    ('host', 'Start/Quit STATghost', 'toggle_host', 'power.png'),
    ('sep_send', '-', None, None),
    ('send', 'Send selection, enclosing function, or statement', 'send_selection', 'send.png'),
    ('function', 'Send enclosing function', 'send_function', 'function.png'),
    ('above', 'Send above (start→caret)', 'send_above', 'above.png'),
    ('below', 'Send below (caret→EOF)', 'send_below', 'below.png'),
    ('chunk', 'Send sniper chunk', 'send_chunk', 'chunk.png'),
    ('source', 'Source file via .paths[4]', 'send_file', 'export.png'),
    ('srcsel', 'Source selection / function via .paths[5]', 'source_selection', 'source-sel.png'),
    ('setwd', 'setwd to file directory', 'set_wd_here', 'setwd.png'),
    ('inspect', 'Print identifier under caret (Inspect extras in the arrow)', 'inspect_print', 'print.png'),
    ('ls', 'ls()', 'inspect_ls', 'ls.png'),
    ('str', 'str() of identifier under caret', 'inspect_str', 'str.png'),
    ('names', 'names() of identifier under caret', 'inspect_names', 'names.png'),
    ('plot', 'plot() of identifier under caret', 'inspect_plot', 'plot.png'),
    ('help', 'help() of identifier under caret', 'inspect_help', 'help_selected.png'),
    ('head', 'head() of identifier under caret', 'inspect_head', 'print_head.png'),
    ('tail', 'tail() of identifier under caret', 'inspect_tail', 'print_tail.png'),
    ('clear', 'Clear STATghost Console', 'clear_console', 'clear.png'),
    ('close_graphics', 'graphics.off()', 'inspect_graphics_off', 'close_graphics.png'),
    ('remove_objects', 'rm(list=ls())', 'inspect_rm_all', 'remove_objects.png'),
    ('clear_all', 'Clear Console, rm(list=ls()), graphics.off()', 'inspect_clear_all', 'clear_all.png'),
    ('sep_edit', '-', None, None),
    ('assign', 'Insert <-', 'insert_assign', 'assign.png'),
    ('pipe', 'Insert pipe', 'insert_pipe', 'pipe.png'),
    ('outline', 'Document outline', 'show_outline', 'outline.png'),
)

_SIDE_CAP = {
    'cfg': 'Config',
    'arm': 'Idle',
    'host': 'Start',
    'send': 'Send',
    'function': 'Function',
    'above': 'Above',
    'below': 'Below',
    'chunk': 'Chunk',
    'source': 'Source',
    'srcsel': 'Src sel',
    'setwd': 'setwd',
    'inspect': 'Inspect',
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
    'assign': '<-',
    'pipe': 'Pipe',
    'outline': 'Outline',
}
_SIDE = tuple(
    (name, _SIDE_CAP.get(name, name), method, icon)
    for name, _hint, method, icon in _TB
    if method is not None
)

def _icon_load(path, fname, rgb):
    """Tint every glyph (masks in res/; no hue left in the PNG)."""
    try:
        return icontint.tinted_path(path, rgb)
    except Exception:
        return path


def _tb_rows_full():
    return chrome_show.filter_toolbar_rows(_TB, prefs.get_chrome_show())


def _tb_rows_now():
    return chrome_show.collapse_nested_rows(_tb_rows_full())


def _tb_names_now():
    return tuple(row[0] for row in _tb_rows_now())


_LEGACY_CAPS = (
    'Send to STATghost',
    'Send current line',
    'Toggle Arm/Idle',
    'Start/Quit STATghost',
    'Show/Hide sniper bar',
    'Config…',
    'Config...',
)


def _here():
    return os.path.dirname(os.path.realpath(__file__))


def _png_dir():
    """Canonical glyphs: plugin res/, else repo shared/res, else png/."""
    here = _here()
    local = os.path.join(here, 'res')
    if os.path.isdir(os.path.join(local, '16px')):
        return local
    shared = os.path.normpath(os.path.join(here, '..', '..', '..', 'shared', 'res'))
    if os.path.isdir(os.path.join(shared, '16px')):
        return shared
    return os.path.join(here, 'png')


def _icon_folder(px):
    if px >= 32:
        return '32px'
    if px >= 24:
        return '24px'
    return '16px'


def _cap_plain(item):
    cap = ''
    if isinstance(item, dict):
        cap = item.get('cap') or item.get('caption') or ''
    return cap.replace('&', '')


def _item_id(item):
    if isinstance(item, dict):
        return item.get('id') or item.get('Id')
    return None


def _item_tag(item):
    if isinstance(item, dict):
        return item.get('tag') or ''
    return ''


def _ui_color(name, fallback):
    d = app_proc(PROC_THEME_UI_DICT_GET, '') or {}
    item = d.get(name) or {}
    c = item.get('color')
    return c if isinstance(c, int) else fallback


def _rgb(r, g, b):
    return r | (g << 8) | (b << 16)


def _unpack_rgb(c):
    return c & 0xFF, (c >> 8) & 0xFF, (c >> 16) & 0xFF


def _blend_rgb(c1, c2, t):
    """Mix two LCL RGB colors; t=0 → c1, t=1 → c2."""
    r1, g1, b1 = _unpack_rgb(c1)
    r2, g2, b2 = _unpack_rgb(c2)
    t = max(0.0, min(1.0, float(t)))
    return _rgb(
        int(r1 + (r2 - r1) * t),
        int(g1 + (g2 - g1) * t),
        int(b1 + (b2 - b1) * t),
    )


def _hdr_band_bg(back, face, border):
    """Slight stripe lift/dip vs TabBg — BG only, not caption colour."""
    r, g, b = _unpack_rgb(back)
    luma = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255.0
    if luma < 0.45:
        lift = face if face != back else _rgb(0x52, 0x52, 0x56)
        return _blend_rgb(back, lift, 0.58)
    shade = border if border != back else _rgb(0xC8, 0xC8, 0xCC)
    return _blend_rgb(back, shade, 0.32)


class Chrome:
    def __init__(self, cmd):
        self.cmd = cmd
        self._armed = False
        self._was_running = False
        self._btns = {}
        self._nest_menus = []
        self._icons = {}
        self._imglist = None
        self._h_dlg = None
        self._h_side_il = None
        self._h_side_list = None
        self._grid_btns = {}
        self._grid_cap_labels = {}
        self._grid_meta = {}
        self._grid_ctl_names = []
        self._grid_bars = []
        self._side_freeze = 0
        self._grid_content_h = 1
        self._side_icon_idx = {}
        self._side_ready = False
        self._timer = False
        self._outline_items = []
        self._outline_hdr = 0  # status lines before outline entries
        self._side_lines = None
        self._arm_paint = None
        self._icons_busy = False
        self._icons_sig = None
        # False while the toolbar is being built — ADD_ITEM must not
        # fire Start/Quit. STATghost never auto-starts with CudaText.
        self._host_cmd_ok = False

    def host_cmd_allowed(self):
        return bool(self._host_cmd_ok)

    def on_start(self):
        # Do not call host.start() here. Side tab opens only if SG
        # is already running (owner: no auto-launch with CudaText).
        remove_legacy_tools()
        self.install_toolbar()
        # [sidebar1] is an empty shell until ADD_DIALOG. Attach now so
        # a click (or a restored session) is not a blank panel.
        self._ensure_side()
        if host.is_running():
            self._was_running = True
            self._armed = False
            self.open_side(activate=True, focus=False)
        else:
            self.refresh()
        self._start_timer()
        self._host_cmd_ok = True

    def open_side(self, activate=True, focus=False):
        self._ensure_side()
        if activate:
            try:
                app_proc(PROC_SHOW_SIDEPANEL_SET, True)
            except Exception:
                pass
            app_proc(PROC_SIDEPANEL_ACTIVATE, (TITLE, bool(focus)))
        self.refresh()

    def is_armed(self):
        return bool(self._armed and host.is_running())

    def note_arm_state(self, armed):
        self._armed = bool(armed and host.is_running())

    def note_host_down(self):
        self._armed = False
        self._was_running = False

    def note_host_up(self):
        self._armed = False
        self._was_running = True

    def tick(self, tag=''):
        running = host.is_running()
        if running and not self._was_running:
            self._armed = False
        if (not running) and self._was_running:
            self._armed = False
        self._was_running = running
        self.refresh()

    def refresh(self):
        running = host.is_running()
        armed = bool(running and self._armed)
        paint = (running, armed)
        if paint != self._arm_paint:
            self._arm_paint = paint
            if 'arm' in self._btns:
                button_proc(
                    self._btns['arm'], BTN_SET_IMAGEINDEX,
                    self._icons.get('armed' if armed else 'idle', -1),
                )
                button_proc(
                    self._btns['arm'], BTN_SET_HINT,
                    'Armed — click to Idle' if armed else 'Idle — click to Arm',
                )
            if 'host' in self._btns:
                button_proc(
                    self._btns['host'], BTN_SET_IMAGEINDEX,
                    self._icons.get('kill' if running else 'power', -1),
                )
                button_proc(
                    self._btns['host'], BTN_SET_HINT,
                    'Quit STATghost' if running else 'Start STATghost',
                )
        self._refresh_side(running, armed)

    def install_toolbar(self):
        try:
            h_bar = app_proc(PROC_GET_MAIN_TOOLBAR, '')
        except Exception:
            return
        if not h_bar:
            return
        self._load_icons(h_bar)
        wanted = _tb_names_now()
        if self._plugin_names(h_bar) != wanted:
            self._drop_plugin_buttons(h_bar)
            self._create_toolbar(h_bar)
        else:
            self._btns = self._scan_toolbar(h_bar)
            self._restyle_seps(h_bar)
        self._apply_imglist()
        toolbar_proc(h_bar, TOOLBAR_UPDATE)

    def rebuild_chrome(self):
        """Re-apply visible buttons after Config (toolbar recreate + side)."""
        self._freeze_side(True)
        try:
            self.install_toolbar()
            self._rebuild_side_buttons()
            self._apply_side_visibility()
            self.refresh()
            for h_bar in self._grid_bars:
                try:
                    toolbar_proc(h_bar, TOOLBAR_UPDATE)
                except Exception:
                    pass
        finally:
            self._freeze_side(False)

    def _freeze_side(self, frozen):
        """Hide/lock the side form while toolbars and the keypad are rebuilt."""
        if frozen:
            self._side_freeze += 1
            if self._side_freeze > 1:
                return
        else:
            self._side_freeze = max(0, self._side_freeze - 1)
            if self._side_freeze:
                return
        if not self._h_dlg:
            return
        try:
            dlg_proc(self._h_dlg, DLG_LOCK if frozen else DLG_UNLOCK)
        except Exception:
            pass
        prop = {'vis': (not frozen), 'en': (not frozen)}
        for name in ('grid_scroll', 'grid'):
            try:
                dlg_proc(self._h_dlg, DLG_CTL_PROP_SET, name=name, prop=prop)
            except Exception:
                pass
        if not frozen:
            self._refresh_side_scroll()

    def _refresh_side_scroll(self):
        """Re-pin keypad height after unfreeze / dock — AutoScroll skipped
        while grid_scroll was hidden (Apply/rebuild freeze)."""
        if not self._h_dlg or self._side_freeze:
            return
        self._size_side_grid(self._grid_content_h)

    def _ensure_side_il(self):
        if self._h_side_il:
            return
        try:
            self._h_side_il = imagelist_proc(0, IMAGELIST_CREATE, value=0)
        except Exception:
            self._h_side_il = None

    def _rebuild_side_buttons(self):
        """Drop and recreate the side-tab analytic keypad."""
        self._ensure_side_il()
        self._side_icon_idx = self._fill_imagelist(self._h_side_il, 16)
        self._fill_side_grid()

    def _clear_side_grid(self):
        """Drop analytic-grid child toolbars (Config rebuild)."""
        if not self._h_dlg:
            self._grid_btns = {}
            self._grid_cap_labels = {}
            self._grid_meta = {}
            self._grid_ctl_names = []
            self._grid_bars = []
            return
        for name in self._grid_ctl_names:
            try:
                dlg_proc(self._h_dlg, DLG_CTL_DELETE, name=name)
            except Exception:
                pass
        self._grid_btns = {}
        self._grid_cap_labels = {}
        self._grid_meta = {}
        self._grid_ctl_names = []
        self._grid_bars = []

    def _grid_add(self, kind, prop):
        """Add a named child of the analytic `grid` panel."""
        n = dlg_proc(self._h_dlg, DLG_CTL_ADD, kind)
        dlg_proc(self._h_dlg, DLG_CTL_PROP_SET, index=n, prop=prop)
        name = prop.get('name')
        if name:
            self._grid_ctl_names.append(name)
        return dlg_proc(self._h_dlg, DLG_CTL_HANDLE, index=n)

    def _theme_bar(self, h_bar):
        """Copy ATFlatTheme (same tokens as the main CudaText toolbar)."""
        if not h_bar:
            return
        try:
            toolbar_proc(h_bar, TOOLBAR_THEME)
            toolbar_proc(h_bar, TOOLBAR_UPDATE)
        except Exception:
            pass

    def _ctl_theme(self, name, color=None, font_color=None, font_style=None):
        if not self._h_dlg or not name:
            return
        prop = {}
        if color is not None:
            prop['color'] = color
        if font_color is not None:
            prop['font_color'] = font_color
        if font_style is not None:
            prop['font_style'] = font_style
        if not prop:
            return
        try:
            dlg_proc(self._h_dlg, DLG_CTL_PROP_SET, name=name, prop=prop)
        except Exception:
            pass

    def _grid_rule(self, idx, parent):
        """Hairline under the family title (between title and keys)."""
        pal = self._palette()
        name = 'grid_rule_%d' % idx
        self._grid_add('panel', {
            'name': name,
            'p': parent,
            'align': ALIGN_TOP,
            'h': GRID_RULE_H,
            'sp_l': 6,
            'sp_r': 6,
            'sp_t': 1,
            'sp_b': 1,
            'color': pal['border'],
        })

    def _grid_hdr(self, title, idx, parent):
        pal = self._palette()
        band = 'grid_hdr_band_%d' % idx
        self._grid_add('panel', {
            'name': band,
            'p': parent,
            'align': ALIGN_TOP,
            'h': GRID_HDR_H,
            'sp_l': 2,
            'sp_r': 2,
            'sp_t': 1,
            'sp_b': 0,
            'color': pal['hdr_band'],
        })
        self._grid_add('label', {
            'name': 'grid_hdr_%d' % idx,
            'p': band,
            'align': ALIGN_CLIENT,
            'cap': '  ' + title.upper(),
            'sp_l': 4,
            'sp_t': 1,
            'color': pal['hdr_band'],
            'font_color': pal['muted'],
            'font_style': 'b',
        })

    def _grid_metrics(self):
        """cell_w, row_h for the current chrome.grid_label pref.

        below: width = longest GRID_CAP + 20% (chrome_show.grid_cell_w).
        Cells still stretch equal via a_l/a_r; this is the placeholder
        so gtk2/win32 pack Source|Sel apart before anchors fire.
        """
        mode = prefs.get_grid_label()
        ph_w, row_h = _GRID_METRICS.get(mode, _GRID_METRICS['below'])
        if mode == 'below':
            return chrome_show.grid_cell_w(), row_h
        return ph_w, row_h

    def _side_panel_min_w(self):
        cell_w, _row_h = self._grid_metrics()
        return chrome_show.grid_panel_min_w(cell_w)

    def _apply_side_min_width(self):
        """Keep keypad cells wide enough — dialog w_min + scroll child."""
        if not self._h_dlg:
            return
        min_w = self._side_panel_min_w()
        try:
            dlg_proc(self._h_dlg, DLG_PROP_SET, prop={'w_min': min_w})
        except Exception:
            pass
        for name in ('grid_scroll', 'grid'):
            try:
                dlg_proc(self._h_dlg, DLG_CTL_PROP_SET, name=name, prop={
                    'w_min': min_w,
                })
            except Exception:
                pass

    def _grid_cell_props(self, row_name, col, cell_w, row_h):
        """Placeholder size until siblings exist and a_l/a_r can bind."""
        pal = self._palette()
        return {
            'name': 'gc_%s_%d' % (row_name, col),
            'p': row_name,
            'x': 4 + col * cell_w,
            'y': 1,
            'w': cell_w,
            'h': row_h - 2,
            'color': pal['back'],
        }

    def _grid_bind_row(self, row_name, cols):
        """Equal cells: bind a_l/a_r only after every sibling name exists.

        Inner gutter 3+3 so adjacent captions (Source|Sel) do not run
        together; outer 4 matches the card edge.
        """
        last = cols - 1
        for col in range(cols):
            prev = 'gc_%s_%d' % (row_name, col - 1)
            nxt = 'gc_%s_%d' % (row_name, col + 1)
            name = 'gc_%s_%d' % (row_name, col)
            if col == 0:
                prop = {
                    'a_l': ('', '['),
                    'a_r': (nxt, '['),
                    'sp_l': 4,
                    'sp_r': 3,
                }
            elif col == last:
                prop = {
                    'a_l': (prev, ']'),
                    'a_r': ('', ']'),
                    'sp_l': 3,
                    'sp_r': 4,
                }
            else:
                prop = {
                    'a_l': (prev, ']'),
                    'a_r': (nxt, '['),
                    'sp_l': 3,
                    'sp_r': 3,
                }
            try:
                dlg_proc(self._h_dlg, DLG_CTL_PROP_SET, name=name, prop=prop)
            except Exception:
                pass

    def _apply_grid_label(self, hb, key):
        """KIND + caption — below uses icon-only + themed label under the glyph."""
        if not hb:
            return
        cap, hint = self._grid_meta.get(key, (key, key))
        mode = prefs.get_grid_label()
        cell_w, _row_h = self._grid_metrics()
        if mode == 'icon':
            button_proc(hb, BTN_SET_KIND, BTNKIND_ICON_ONLY)
            button_proc(hb, BTN_SET_TEXT, '')
            button_proc(hb, BTN_SET_BOLD, False)
            self._sync_grid_caption(key, '')
        else:
            button_proc(hb, BTN_SET_KIND, BTNKIND_ICON_ONLY)
            button_proc(hb, BTN_SET_TEXT, '')
            button_proc(hb, BTN_SET_BOLD, False)
            self._sync_grid_caption(key, cap)
        button_proc(hb, BTN_SET_HINT, hint)
        try:
            button_proc(hb, BTN_SET_WIDTH, max(24, cell_w - 8))
        except Exception:
            pass

    def _sync_grid_caption(self, key, cap):
        """High-contrast caption label (below mode) — same FG logic as icons."""
        name = self._grid_cap_labels.get(key)
        if not name or not self._h_dlg:
            return
        pal = self._palette()
        try:
            dlg_proc(self._h_dlg, DLG_CTL_PROP_SET, name=name, prop={
                'cap': cap,
                'color': pal['back'],
                'font_color': pal['caption'],
            })
        except Exception:
            pass

    def _polish_grid_keys(self):
        for key, hb in self._grid_btns.items():
            try:
                self._apply_grid_label(hb, key)
            except Exception:
                pass

    def _fill_grid_key(self, h_bar, key, methods, hints, il, icons):
        method = methods.get(key)
        if not method:
            return
        toolbar_proc(h_bar, TOOLBAR_ADD_ITEM)
        cnt = toolbar_proc(h_bar, TOOLBAR_GET_COUNT) or 0
        hb = toolbar_proc(h_bar, TOOLBAR_GET_BUTTON_HANDLE, index=cnt - 1)
        if not hb:
            return
        cap = chrome_show.GRID_CAP.get(key, _SIDE_CAP.get(key, key))
        hint = hints.get(key, cap)
        self._grid_meta[key] = (cap, hint)
        self._apply_grid_label(hb, key)
        if il:
            button_proc(hb, BTN_SET_IMAGELIST, il)
        button_proc(hb, BTN_SET_IMAGEINDEX, icons.get(key, -1))
        button_proc(
            hb, BTN_SET_DATA1,
            'module=cuda_statghost;cmd=' + method + ';',
        )
        self._grid_btns[key] = hb

    def _grid_families(self, plan):
        """Group grid_plan into (title, row-tuples) — Host first."""
        families = []
        title = None
        rows = []
        for kind, payload in plan:
            if kind == 'hdr':
                if title is not None:
                    families.append((title, tuple(rows)))
                title = payload
                rows = []
            elif kind == 'row':
                rows.append(tuple(payload))
        if title is not None:
            families.append((title, tuple(rows)))
        return families

    def _fill_grid_row(self, parent, row_i, keys, cols, methods, hints, il, icons):
        keys = tuple(keys) + (None,) * (cols - len(keys))
        mode = prefs.get_grid_label()
        cell_w, row_h = self._grid_metrics()
        cap_h = GRID_CAP_H if mode == 'below' else 0
        row_name = 'grid_row_%d' % row_i
        pal = self._palette()
        self._grid_add('panel', {
            'name': row_name,
            'p': parent,
            'align': ALIGN_TOP,
            'h': row_h,
            'color': pal['back'],
        })
        for col in range(cols):
            self._grid_add('panel', self._grid_cell_props(row_name, col, cell_w, row_h))
        self._grid_bind_row(row_name, cols)
        for col, key in enumerate(keys):
            if not key:
                continue
            cell = 'gc_%s_%d' % (row_name, col)
            tb_name = 'gt_%s_%d' % (row_name, col)
            tb_prop = {
                'name': tb_name,
                'p': cell,
                'align': ALIGN_TOP if mode == 'below' else ALIGN_CLIENT,
            }
            if mode == 'below':
                tb_prop['h'] = max(GRID_ICON_STRIP_H, row_h - cap_h)
            h_bar = self._grid_add('toolbar', tb_prop)
            if not h_bar:
                continue
            self._grid_bars.append(h_bar)
            try:
                toolbar_proc(h_bar, TOOLBAR_SET_VERTICAL, index=False)
                toolbar_proc(h_bar, TOOLBAR_SET_WRAP, index=False)
            except Exception:
                pass
            self._theme_bar(h_bar)
            self._fill_grid_key(h_bar, key, methods, hints, il, icons)
            self._theme_bar(h_bar)
            if mode == 'below':
                cap = chrome_show.GRID_CAP.get(key, _SIDE_CAP.get(key, key))
                cap_name = 'gl_%s_%d' % (row_name, col)
                self._grid_add('label', {
                    'name': cap_name,
                    'p': cell,
                    'align': ALIGN_BOTTOM,
                    'h': cap_h,
                    'sp_l': 2,
                    'sp_r': 2,
                    'sp_t': 0,
                    'sp_b': 1,
                    'color': pal['back'],
                    'font_color': pal['caption'],
                    'cap': cap,
                })
                self._grid_cap_labels[key] = cap_name
            if key in self._grid_btns:
                self._apply_grid_label(self._grid_btns[key], key)

    def _size_side_grid(self, total_h):
        """Pin keypad height for scrollbox AutoScroll (must be Align=None).

        LCL/VCL CalcAutoRange ignores Align≠alNone children, so ALIGN_TOP
        inside the scrollbox never raises VertScrollBar — even when h is
        larger than the client. Absolute x/y/h + left/right anchors match
        cuda_testing_canvas_proc. Re-apply after unfreeze so the bar
        recalculates when the scrollbox is visible again.
        """
        if not self._h_dlg:
            return
        h = max(1, int(total_h))
        self._grid_content_h = h
        min_w = self._side_panel_min_w()
        prop = {
            'align': ALIGN_NONE,
            'x': 0,
            'y': 0,
            'h': h,
            'h_min': h,
            'w_min': min_w,
            'a_l': ('', '['),
            'a_r': ('', ']'),
            'sp_l': 2,
            'sp_r': 2,
            'sp_t': 2,
            'sp_b': 2,
        }
        try:
            sc = dlg_proc(self._h_dlg, DLG_CTL_PROP_GET, name='grid_scroll') or {}
            sw = int(sc.get('w') or 0)
            prop['w'] = max(min_w, sw) if sw > 0 else min_w
        except Exception:
            prop['w'] = min_w
        try:
            dlg_proc(self._h_dlg, DLG_CTL_PROP_SET, name='grid', prop=prop)
        except Exception:
            pass
        self._apply_side_min_width()

    def _fill_side_grid(self):
        """Family cards: title above keys (LCL alTop = last child on top).

        Toolbar DATA1 (not button_ex on_change): the side form is
        reparented, so gtk2 bound clicks stay dead. Existing 16px glyphs;
        24/32 is a later pass.
        """
        if not self._h_dlg:
            return
        total_h = 1
        self._freeze_side(True)
        try:
            total_h = self._fill_side_grid_body()
        finally:
            self._freeze_side(False)

    def _fill_side_grid_body(self):
        self._clear_side_grid()
        methods = {row[0]: row[2] for row in _SIDE}
        hints = {row[0]: row[1] for row in _TB if row[2] is not None}
        plan = chrome_show.grid_plan(prefs.get_chrome_show())
        cols = chrome_show.GRID_COLS
        il = self._h_side_il
        icons = self._side_icon_idx
        families = self._grid_families(plan)
        # Last alTop sibling sits at the top edge — add Edit first, Host last.
        row_i = 0
        row_index = {}
        for title, rows in families:
            for _keys in rows:
                row_index[(title, _keys)] = row_i
                row_i += 1
        total_h = 4  # grid sp_t + sp_b
        for fam_i, (title, rows) in enumerate(reversed(families)):
            visual_i = len(families) - 1 - fam_i
            card = 'grid_card_%d' % visual_i
            _cell_w, row_h = self._grid_metrics()
            card_h = (
                GRID_HDR_H + GRID_RULE_H + len(rows) * row_h + 6
            )
            total_h += card_h + 1  # card + sp_b
            pal = self._palette()
            self._grid_add('panel', {
                'name': card,
                'p': 'grid',
                'align': ALIGN_TOP,
                'h': card_h,
                'sp_t': 0,
                'sp_b': 1,
                'color': pal['back'],
            })
            # Inside the card: keys first, hairline, header last → title on top.
            for keys in reversed(rows):
                self._fill_grid_row(
                    card, row_index[(title, keys)], keys, cols,
                    methods, hints, il, icons,
                )
            self._grid_rule(visual_i, card)
            self._grid_hdr(title, visual_i, card)
        # Cards use ALIGN_TOP inside `grid`; `grid` itself stays Align=None
        # so the scrollbox can measure overflow (see _size_side_grid).
        self._grid_content_h = max(1, int(total_h))
        self._apply_side_theme()
        return total_h

    def _create_toolbar(self, h_bar):
        self._btns = {}
        self._nest_menus = []
        methods = {row[0]: row[2] for row in _TB if row[2] is not None}
        show = prefs.get_chrome_show()
        for name, hint, method, icon in _tb_rows_now():
            h_btn = toolbar_proc(h_bar, TOOLBAR_ADD_ITEM)
            if h_btn is None:
                cnt = toolbar_proc(h_bar, TOOLBAR_GET_COUNT)
                h_btn = toolbar_proc(h_bar, TOOLBAR_GET_BUTTON_HANDLE, index=cnt - 1)
            if not h_btn:
                continue
            button_proc(h_btn, BTN_SET_DATA2, TAG + ':' + name)
            if icon is None:
                self._style_sep(h_btn)
                continue
            button_proc(h_btn, BTN_SET_KIND, BTNKIND_ICON_ONLY)
            button_proc(h_btn, BTN_SET_HINT, hint)
            idx = self._icons.get(icon, -1)
            button_proc(h_btn, BTN_SET_IMAGEINDEX, idx)
            button_proc(
                h_btn, BTN_SET_DATA1,
                'module=cuda_statghost;cmd=' + method + ';',
            )
            self._attach_nest_menu(h_btn, name, methods, show)
            self._btns[name] = h_btn

    def _attach_nest_menu(self, h_btn, name, methods, show):
        """Tinn-style nested extras: click = parent, arrow = related cmds."""
        kids = chrome_show.nest_menu_keys(name, show)
        if not kids:
            return
        try:
            h_menu = menu_proc(0, MENU_CREATE)
        except Exception:
            return
        if not h_menu:
            return
        for kid in kids:
            method = methods.get(kid)
            if not method:
                continue
            cap = _SIDE_CAP.get(kid, kid)
            menu_proc(
                h_menu, MENU_ADD,
                command='module=cuda_statghost;cmd=' + method + ';',
                caption=cap,
            )
        try:
            button_proc(h_btn, BTN_SET_MENU, h_menu)
            button_proc(h_btn, BTN_SET_ARROW, True)
        except Exception:
            return
        self._nest_menus.append(h_menu)

    def _drop_plugin_buttons(self, h_bar):
        """Drop every plugin-tagged button (old order, leftover Line, seps)."""
        try:
            n = toolbar_proc(h_bar, TOOLBAR_GET_COUNT) or 0
        except Exception:
            return
        for i in range(n - 1, -1, -1):
            h_btn = toolbar_proc(h_bar, TOOLBAR_GET_BUTTON_HANDLE, index=i)
            if not h_btn:
                continue
            data2 = button_proc(h_btn, BTN_GET_DATA2) or ''
            if data2.startswith(TAG + ':'):
                toolbar_proc(h_bar, TOOLBAR_DELETE_BUTTON, index=i)

    def _style_sep(self, h_btn):
        # Same as TATFlatToolbar.AddSep on a horizontal bar: Kind=SepHorz
        # (thin vertical line). SepVert is the other orientation.
        button_proc(h_btn, BTN_SET_KIND, BTNKIND_SEP_HORZ)
        button_proc(h_btn, BTN_SET_ENABLED, False)

    def _restyle_seps(self, h_bar):
        try:
            n = toolbar_proc(h_bar, TOOLBAR_GET_COUNT) or 0
        except Exception:
            return
        for i in range(n):
            h_btn = toolbar_proc(h_bar, TOOLBAR_GET_BUTTON_HANDLE, index=i)
            if not h_btn:
                continue
            data2 = button_proc(h_btn, BTN_GET_DATA2) or ''
            if data2 in (TAG + ':sep', TAG + ':sep_send', TAG + ':sep_edit') or (
                data2.startswith(TAG + ':sep')
            ):
                self._style_sep(h_btn)

    def _plugin_names(self, h_bar):
        names = []
        try:
            n = toolbar_proc(h_bar, TOOLBAR_GET_COUNT) or 0
        except Exception:
            return tuple()
        for i in range(n):
            h_btn = toolbar_proc(h_bar, TOOLBAR_GET_BUTTON_HANDLE, index=i)
            if not h_btn:
                continue
            data2 = button_proc(h_btn, BTN_GET_DATA2) or ''
            if data2.startswith(TAG + ':'):
                names.append(data2.split(':', 1)[1])
        return tuple(names)

    def _scan_toolbar(self, h_bar):
        found = {}
        try:
            n = toolbar_proc(h_bar, TOOLBAR_GET_COUNT) or 0
        except Exception:
            return found
        for i in range(n):
            h_btn = toolbar_proc(h_bar, TOOLBAR_GET_BUTTON_HANDLE, index=i)
            if not h_btn:
                continue
            data2 = button_proc(h_btn, BTN_GET_DATA2) or ''
            if not data2.startswith(TAG + ':'):
                continue
            name = data2.split(':', 1)[1]
            if not name.startswith('sep'):
                found[name] = h_btn
        return found

    def reload_icons(self):
        """Re-tint toolbar + side glyphs (theme change or Config icons FG).

        Skip if already loading (THEME_UI can fire from TOOLBAR_UPDATE) or
        if pixel size + theme tag did not change — otherwise idle/armed
        imagelist swaps can TDR a weak GPU.
        """
        if self._icons_busy:
            return
        try:
            h_bar = app_proc(PROC_GET_MAIN_TOOLBAR, '')
        except Exception:
            h_bar = None
        px = 16
        if h_bar:
            host_list = toolbar_proc(h_bar, TOOLBAR_GET_IMAGELIST)
            if host_list:
                size = imagelist_proc(host_list, IMAGELIST_GET_SIZE)
                if isinstance(size, (tuple, list)) and size:
                    px = int(size[0])
        try:
            sig = (px, icontint.theme_tag())
        except Exception:
            sig = (px, None)
        if sig == self._icons_sig:
            return
        self._icons_busy = True
        try:
            self._load_icons(h_bar)
            self._apply_imglist()
            self._reload_side_icons()
            self._apply_side_theme()
            self._refresh_side_scroll()
            self._arm_paint = None
            self._side_lines = None
            self._icons_sig = sig
            self.refresh()
            if h_bar:
                toolbar_proc(h_bar, TOOLBAR_UPDATE)
            for h_sb in self._grid_bars:
                try:
                    toolbar_proc(h_sb, TOOLBAR_UPDATE)
                except Exception:
                    pass
        finally:
            self._icons_busy = False

    def _apply_imglist(self):
        if not self._imglist:
            return
        running = False
        try:
            running = host.is_running()
        except Exception:
            pass
        armed = bool(running and self._armed)
        for name, h_btn in self._btns.items():
            button_proc(h_btn, BTN_SET_IMAGELIST, self._imglist)
            if name == 'arm':
                key = 'armed' if armed else 'idle'
            elif name == 'host':
                key = 'kill' if running else 'power'
            else:
                key = name
            button_proc(h_btn, BTN_SET_IMAGEINDEX, self._icons.get(key, -1))

    def _glyph_map(self):
        """name → png filename for static glyphs (+ armed/kill swaps)."""
        files = {
            'armed': 'armed.png',
            'idle': 'idle.png',
            'power': 'power.png',
            'kill': 'kill.png',
        }
        for name, _hint, method, icon in _TB:
            if method is not None and icon:
                files[name] = icon
                files[icon] = icon
        return files

    def _load_icons(self, h_bar):
        px = 16
        if h_bar:
            host_list = toolbar_proc(h_bar, TOOLBAR_GET_IMAGELIST)
            if host_list:
                size = imagelist_proc(host_list, IMAGELIST_GET_SIZE)
                if isinstance(size, (tuple, list)) and size:
                    px = int(size[0])
        if self._imglist is None:
            self._imglist = imagelist_proc(0, IMAGELIST_CREATE, value=0)
        try:
            imagelist_proc(self._imglist, IMAGELIST_DELETE_ALL)
        except Exception:
            pass
        imagelist_proc(self._imglist, IMAGELIST_SET_SIZE, (px, px))
        folder = os.path.join(_png_dir(), _icon_folder(px))
        rgb = icontint.theme_rgb(prefs.get_icons_fg())
        for key, fname in self._glyph_map().items():
            path = os.path.join(folder, fname)
            idx = -1
            if os.path.isfile(path):
                load = _icon_load(path, fname, rgb)
                try:
                    idx = imagelist_proc(self._imglist, IMAGELIST_ADD, value=load)
                except Exception:
                    idx = -1
                if idx is None:
                    idx = -1
            self._icons[key] = idx
            self._icons[fname] = idx

    def _fill_imagelist(self, il, px):
        """Load the side-tab glyphs into *il*. Returns name → index."""
        out = {}
        if not il:
            return out
        try:
            imagelist_proc(il, IMAGELIST_DELETE_ALL)
        except Exception:
            pass
        imagelist_proc(il, IMAGELIST_SET_SIZE, (px, px))
        folder = os.path.join(_png_dir(), _icon_folder(px))
        files = dict(self._glyph_map())
        rgb = icontint.theme_rgb(prefs.get_icons_fg())
        for key, fname in files.items():
            path = os.path.join(folder, fname)
            idx = -1
            if os.path.isfile(path):
                load = _icon_load(path, fname, rgb)
                try:
                    idx = imagelist_proc(il, IMAGELIST_ADD, value=load)
                except Exception:
                    idx = -1
                if idx is None:
                    idx = -1
            out[key] = idx
        return out

    def _reload_side_icons(self):
        """Re-tint side-tab imagelist after theme / icons-FG change."""
        if not self._h_side_il:
            return
        side_icons = self._fill_imagelist(self._h_side_il, 16)
        self._side_icon_idx = side_icons
        for name, hb in self._grid_btns.items():
            if name in ('arm', 'host'):
                continue
            button_proc(hb, BTN_SET_IMAGEINDEX, side_icons.get(name, -1))
        # arm/host indices follow Armed/Idle state in refresh()

    def _ensure_side(self):
        if self._side_ready and self._h_dlg:
            return
        # gtk2: dlg_proc button_ex on_change is ignored until TFormDummy
        # DoShow sets IsFormShownAlready. A side-panel form is reparented
        # (not DLG_SHOW), so those clicks stay dead. Toolbar DATA1 is the
        # same path as the main CudaText bar, which already works here.
        h = dlg_proc(0, DLG_CREATE)
        if not h:
            print('STATghost side: DLG_CREATE failed')
            msg_status(PLUGIN + ': side tab — DLG_CREATE failed')
            return
        self._h_dlg = h
        pal = self._palette()
        dlg_proc(h, DLG_PROP_SET, prop={'cap': TITLE, 'color': pal['back']})
        # Footer starts collapsed. TATListbox (listbox_ex) paints TreeBg —
        # a pale paper island. LCL listbox + TabBg, shown only for outline.
        n = dlg_proc(h, DLG_CTL_ADD, 'panel')
        dlg_proc(h, DLG_CTL_PROP_SET, index=n, prop={
            'name': 'status_band',
            'align': ALIGN_BOTTOM,
            'h': 0,
            'vis': False,
            'color': pal['back'],
        })
        n = dlg_proc(h, DLG_CTL_ADD, 'listbox')
        dlg_proc(h, DLG_CTL_PROP_SET, index=n, prop={
            'name': 'status',
            'p': 'status_band',
            'align': ALIGN_CLIENT,
            'color': pal['back'],
            'font_color': pal['muted'],
            'on_click_dbl': 'module=cuda_statghost;cmd=outline_jump;',
        })
        self._h_side_list = dlg_proc(h, DLG_CTL_HANDLE, index=n)
        self._ensure_side_il()
        self._side_icon_idx = self._fill_imagelist(self._h_side_il, 16)
        # Child of scrollbox must be Align=None + explicit h: LCL AutoScroll
        # skips aligned controls, so ALIGN_TOP/CLIENT never shows the vert
        # bar (Win32 + gtk2). Pattern: cuda_testing_canvas_proc / dlg_proc
        # test_scrollbox (absolute x/y/w/h).
        n = dlg_proc(h, DLG_CTL_ADD, 'scrollbox')
        dlg_proc(h, DLG_CTL_PROP_SET, index=n, prop={
            'name': 'grid_scroll',
            'align': ALIGN_CLIENT,
            'border': False,
            'color': pal['back'],
        })
        side_min_w = self._side_panel_min_w()
        n = dlg_proc(h, DLG_CTL_ADD, 'panel')
        dlg_proc(h, DLG_CTL_PROP_SET, index=n, prop={
            'name': 'grid',
            'p': 'grid_scroll',
            'align': ALIGN_NONE,
            'x': 0,
            'y': 0,
            'w': side_min_w,
            'h': 1,
            'h_min': 1,
            'w_min': side_min_w,
            'a_l': ('', '['),
            'a_r': ('', ']'),
            'sp_l': 2,
            'sp_r': 2,
            'sp_t': 2,
            'sp_b': 2,
            'color': pal['back'],
        })
        self._fill_side_grid()
        self._apply_side_visibility()
        icon = os.path.join(_png_dir(), '24px', 'statghost_24.png')
        if not os.path.isfile(icon):
            icon = os.path.join(_png_dir(), 'statghost_24.png')
        ok = app_proc(PROC_SIDEPANEL_ADD_DIALOG, (TITLE, h, icon))
        print('STATghost side: dlg=%s ADD_DIALOG=%s' % (h, ok))
        if not ok:
            msg_status(PLUGIN + ': side tab — ADD_DIALOG failed')
            return
        # Docking changes client size — size after the side viewport exists.
        self._refresh_side_scroll()
        self._side_ready = True

    def jump_outline_selection(self):
        """Double-click on side list: jump to outline line (skip status hdr)."""
        if not self._h_side_list or not self._outline_items:
            return
        prop = dlg_proc(self._h_dlg, DLG_CTL_PROP_GET, name='status') or {}
        idx = prop.get('val')
        if idx is None:
            return
        try:
            idx = int(idx)
        except (TypeError, ValueError):
            return
        oi = idx - int(self._outline_hdr)
        if oi < 0 or oi >= len(self._outline_items):
            return
        line = int(self._outline_items[oi]['line'])
        from cudatext import ed
        ed.set_caret(0, line)
        msg_status(PLUGIN + ': outline → L' + str(line + 1))

    def _palette(self):
        """Same UI tokens as ToolbarMain / ATFlatTheme (formmain_themes.inc)."""
        font = _ui_color('ButtonFont', _rgb(0x90, 0x90, 0x90))
        muted = _ui_color('TabFont', font)
        back = _ui_color('TabBg', _ui_color('EdTextBg', _rgb(0x2A, 0x2A, 0x2A)))
        face = _ui_color('ButtonBgPassive', _ui_color('ButtonBg', back))
        border = _ui_color('ButtonBorderPassive', _rgb(0x55, 0x55, 0x55))
        cr, cg, cb = icontint.theme_rgb(prefs.get_icons_fg())
        hdr_band = _hdr_band_bg(back, face, border)
        return {
            'font': font,
            'muted': muted,
            'caption': _rgb(cr, cg, cb),
            'back': back,
            'face': face,
            'hdr_band': hdr_band,
            'border': border,
            'run': _rgb(0x4C, 0xAF, 0x50),
            'arm': _rgb(0xE6, 0xA8, 0x17),
            'stop': _rgb(0xC0, 0x5A, 0x5A),
        }

    def _apply_side_theme(self):
        """Retint side form / cards / TAT toolbars after THEME_UI."""
        if not self._h_dlg:
            return
        pal = self._palette()
        try:
            dlg_proc(self._h_dlg, DLG_PROP_SET, prop={'color': pal['back']})
        except Exception:
            pass
        self._ctl_theme('grid_scroll', pal['back'])
        self._ctl_theme('grid', pal['back'])
        for name in self._grid_ctl_names:
            if name.startswith('grid_hdr_band_'):
                self._ctl_theme(name, pal['hdr_band'])
            elif name.startswith('grid_hdr_'):
                self._ctl_theme(
                    name, pal['hdr_band'], pal['muted'], font_style='b',
                )
            elif name.startswith('grid_rule_'):
                self._ctl_theme(name, pal['border'])
            elif name.startswith('gl_'):
                self._ctl_theme(name, pal['back'], pal['caption'])
            elif name.startswith('gt_'):
                continue
            else:
                self._ctl_theme(name, pal['back'])
        for h_bar in self._grid_bars:
            self._theme_bar(h_bar)
        self._polish_grid_keys()
        self._ctl_theme('status_band', pal['back'])
        self._ctl_theme('status', pal['back'], pal['muted'])

    def _set_status_band(self, lines):
        """Show a compact TabBg outline strip, or hide the empty island."""
        if not self._h_dlg:
            return
        pal = self._palette()
        if not lines:
            try:
                dlg_proc(self._h_dlg, DLG_CTL_PROP_SET, name='status_band', prop={
                    'vis': False,
                    'h': 0,
                    'color': pal['back'],
                })
            except Exception:
                pass
            return
        h = min(STATUS_H_MAX, len(lines) * STATUS_LINE_H + 6)
        if h < STATUS_LINE_H + 6:
            h = STATUS_LINE_H + 6
        try:
            dlg_proc(self._h_dlg, DLG_CTL_PROP_SET, name='status_band', prop={
                'vis': True,
                'h': h,
                'color': pal['back'],
            })
            dlg_proc(self._h_dlg, DLG_CTL_PROP_SET, name='status', prop={
                'items': '\t'.join(lines),
                'color': pal['back'],
                'font_color': pal['muted'],
            })
        except Exception:
            pass

    def _apply_side_visibility(self):
        """Show/hide side-tab actions from the shared chrome.show list."""
        if not self._grid_btns:
            return
        show = set(prefs.get_chrome_show())
        for name, hb in self._grid_btns.items():
            vis = name in show
            try:
                button_proc(hb, BTN_SET_VISIBLE, vis)
            except Exception:
                pass
            cap_name = self._grid_cap_labels.get(name)
            if cap_name:
                try:
                    dlg_proc(self._h_dlg, DLG_CTL_PROP_SET, name=cap_name, prop={
                        'vis': vis,
                    })
                except Exception:
                    pass

    def _refresh_side(self, running, armed):
        arm_cap = 'Armed' if armed else 'Idle'
        host_cap = 'Quit' if running else 'Start'
        arm_idx = self._side_icon_idx.get('armed' if armed else 'arm', -1)
        host_idx = self._side_icon_idx.get('kill' if running else 'host', -1)
        mode = prefs.get_grid_label()
        if 'arm' in self._grid_btns:
            if mode == 'below':
                self._sync_grid_caption('arm', arm_cap)
            button_proc(self._grid_btns['arm'], BTN_SET_IMAGEINDEX, arm_idx)
        if 'host' in self._grid_btns:
            if mode == 'below':
                self._sync_grid_caption('host', host_cap)
            button_proc(self._grid_btns['host'], BTN_SET_IMAGEINDEX, host_idx)
        if not self._h_side_list:
            return
        self._outline_items = []
        try:
            from cudatext import ed as _ed
            nlines = _ed.get_line_count()

            def _gl(i):
                t = _ed.get_text_line(i)
                return t if t else ''

            self._outline_items = sgoutline.collect_outline(_gl, nlines)
        except Exception:
            self._outline_items = []
        if not self._outline_items:
            if self._side_lines:
                self._side_lines = None
            self._outline_hdr = 0
            self._set_status_band(())
            return
        lines = ['— outline —']
        self._outline_hdr = 1
        for it in self._outline_items:
            lines.append(sgoutline.format_caption(it, width=40))
        if lines == self._side_lines:
            return
        self._side_lines = list(lines)
        self._set_status_band(lines)

    def _start_timer(self):
        if self._timer:
            return
        timer_proc(
            TIMER_START,
            'module=cuda_statghost;cmd=chrome_tick;',
            TICK_MS,
        )
        self._timer = True


_chrome = None


def get(cmd=None):
    global _chrome
    if _chrome is None:
        _chrome = Chrome(cmd)
    elif cmd is not None:
        _chrome.cmd = cmd
    return _chrome


def remove_legacy_tools():
    """Drop the non-standard top-level Tools menu from the experimental bar."""
    try:
        items = menu_proc('top', MENU_ENUM) or []
    except Exception:
        return
    if not isinstance(items, list):
        return
    for it in items:
        if _cap_plain(it) != TOOLS_CAP:
            continue
        tid = _item_id(it)
        if not tid:
            continue
        ours = _item_tag(it) == TAG
        try:
            kids = menu_proc(tid, MENU_ENUM) or []
        except Exception:
            kids = []
        if isinstance(kids, list):
            for k in kids:
                ktag = _item_tag(k)
                kcap = _cap_plain(k)
                if ktag == TAG or kcap in _LEGACY_CAPS:
                    kid = _item_id(k)
                    if kid:
                        try:
                            menu_proc(kid, MENU_REMOVE)
                        except Exception:
                            pass
                    ours = True
        if ours:
            try:
                left = menu_proc(tid, MENU_ENUM) or []
            except Exception:
                left = []
            if not left:
                try:
                    menu_proc(tid, MENU_REMOVE)
                except Exception:
                    pass
        return
