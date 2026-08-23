# Plugin Config — tree (left) + page (right) + Apply/OK/Cancel footer.
# dlg_proc, not dlg_custom: room to grow without stacking / overlapping.
# Nav width: longest caption + 20% slack + gutter (not a fixed 150px).
# Button callbacks are `module=…;cmd=…` strings — gtk2 bound methods never
# fired (OK/Cancel painted dead). D45: Cancel is the default button.
# Checklist stays one checklistbox (not 26 TCheckBox) — GDI/TDR.

from __future__ import annotations

import os

from cudatext import ALIGN_BOTTOM
from cudatext import ALIGN_CLIENT
from cudatext import ALIGN_LEFT
from cudatext import ALIGN_TOP
from cudatext import DBORDER_SIZE
from cudatext import DLG_CREATE
from cudatext import DLG_CTL_ADD
from cudatext import DLG_CTL_DELETE
from cudatext import DLG_CTL_FOCUS
from cudatext import DLG_CTL_HANDLE
from cudatext import DLG_CTL_PROP_GET
from cudatext import DLG_CTL_PROP_SET
from cudatext import DLG_FREE
from cudatext import DLG_HIDE
from cudatext import DLG_PROP_SET
from cudatext import DLG_SCALE
from cudatext import DLG_SHOW_MODAL
from cudatext import PROC_ENUM_ENCODINGS
from cudatext import TREE_ITEM_ADD
from cudatext import TREE_ITEM_GET_PROPS
from cudatext import TREE_ITEM_GET_SELECTED
from cudatext import TREE_ITEM_SELECT
from cudatext import TREE_PROP_SHOW_ROOT
from cudatext import TREE_THEME
from cudatext import app_proc
from cudatext import dlg_file
from cudatext import dlg_proc
from cudatext import msg_status
from cudatext import tree_proc

try:
    from . import chrome_show
    from . import host
    from . import prefs
except ImportError:
    import chrome_show
    import host
    import prefs

PLUGIN = 'STATghost'
_CB = 'module=cuda_statghost;cmd=config_dlg;info=%s;'

PAGES = ('Send', 'Chrome', 'Host')

_SHOW_DEFS = (
    ('cfg', 'Config'),
    ('arm', 'Arm/Idle'),
    ('host', 'Start/Quit'),
    ('send', 'Send'),
    ('function', 'Function'),
    ('above', 'Above'),
    ('below', 'Below'),
    ('chunk', 'Chunk'),
    ('source', 'Source'),
    ('srcsel', 'Src sel/fn'),
    ('setwd', 'setwd'),
    ('inspect', 'Inspect'),
    ('ls', 'ls()'),
    ('str', 'str()'),
    ('names', 'names()'),
    ('plot', 'plot()'),
    ('help', 'Help'),
    ('head', 'head()'),
    ('tail', 'tail()'),
    ('clear', 'Clear'),
    ('close_graphics', 'graphics.off'),
    ('remove_objects', 'rm all'),
    ('clear_all', 'Clear all'),
    ('assign', 'Insert <-'),
    ('pipe', 'Insert pipe'),
    ('outline', 'Outline'),
)
_SHOW_KEYS = tuple(k for k, _c in _SHOW_DEFS)

_PIPE_ITEMS = ('|>  (native R 4.1+)', '%>%  (magrittr)')
_ICONS_FG_ITEMS = (
    'auto  (palette vs theme)',
    'white  (closed white)',
    'graphite',
    'gray  (mid)',
    'theme  (ButtonFont raw)',
)
_ICONS_FG_KEYS = ('auto', 'light', 'dark', 'gray', 'theme')
_GRID_LABEL_ITEMS = (
    'below  (caption under icon)',
    'icon  (icon only, hint on hover)',
)
_GRID_LABEL_KEYS = chrome_show.GRID_LABELS

_FALLBACK_ENCS = (
    'utf-8',
    'utf-16 le',
    'utf-16 be',
    'cp1252',
    'iso-8859-1',
    'latin1',
    'cp850',
    'koi8-r',
)

_W = 640
_H = 500
_FOOT = 48
_TREE_SLACK = 1.20  # longest caption + 20% so new nodes do not keep reshaping
_TREE_GUTTER = 24   # indent + border, dialog units (then DLG_SCALE)
_TREE_MIN = 72
_TREE_MAX = 220
_EMU_CHAR = 8       # fallback if label autosize is 0/-1 (gtk2 client)

_h = 0
_h_tree = 0
_items = []
_saved = False
_applied = False
_snapshot = None
_encs = []


def _as_bool(val):
    if val is True or val == 1:
        return True
    if val is False or val == 0:
        return False
    s = str(val if val is not None else '').strip().lower()
    return s in ('1', 'true', 'yes', 'on')


def _cuda_encodings():
    try:
        raw = app_proc(PROC_ENUM_ENCODINGS, '')
    except Exception:
        raw = None
    out = []
    if isinstance(raw, (list, tuple)):
        out = [str(x).strip() for x in raw if str(x).strip()]
    elif isinstance(raw, str) and raw.strip():
        parts = raw.replace('\r', '\n').replace('\t', '\n').split('\n')
        out = [p.strip() for p in parts if p.strip()]
    if not out:
        out = list(_FALLBACK_ENCS)
    low = [e.lower() for e in out]
    for pref in ('utf-8', 'utf8', 'UTF-8'):
        if pref.lower() in low:
            i = low.index(pref.lower())
            if i > 0:
                out.insert(0, out.pop(i))
            break
    return out


def _enc_index(encs, wanted):
    w = (wanted or '').strip().lower().replace('_', '-')
    if not w:
        w = 'utf-8'
    aliases = {
        'utf8': 'utf-8',
        'utf-8 bom': 'utf-8',
        'utf8 bom': 'utf-8',
        'utf-8': 'utf-8',
        'latin-1': 'iso-8859-1',
        'latin1': 'iso-8859-1',
    }
    w = aliases.get(w, w)
    for i, e in enumerate(encs):
        el = e.lower().replace('_', '-')
        if el == w or aliases.get(el, el) == w:
            return i
    for i, e in enumerate(encs):
        if e.lower().startswith('utf-8') or e.lower() == 'utf8':
            return i
    return 0


def _pipe_index():
    tok = prefs.get_pipe_token()
    return 1 if tok == '%>%' else 0


def _icons_fg_index():
    key = prefs.get_icons_fg()
    try:
        return _ICONS_FG_KEYS.index(key)
    except ValueError:
        return 0


def _grid_label_index():
    key = prefs.get_grid_label()
    try:
        return _GRID_LABEL_KEYS.index(key)
    except ValueError:
        return 0


def _show_dict_from_prefs():
    on = set(prefs.get_chrome_show())
    return {key: (key in on) for key, _cap in _SHOW_DEFS}


def nav_width(text_w):
    """Dialog units: measured caption + slack + gutter, clamped."""
    try:
        tw = int(text_w)
    except (TypeError, ValueError):
        tw = 0
    if tw < 0:
        tw = 0
    w = int(round(tw * _TREE_SLACK)) + _TREE_GUTTER
    if w < _TREE_MIN:
        return _TREE_MIN
    if w > _TREE_MAX:
        return _TREE_MAX
    return w


def _measure_caption(h, cap):
    """Real font width via hidden autosize label (gtk2 and win32)."""
    name = '_nav_probe'
    try:
        _add(h, 'label', {
            'name': name,
            'cap': cap,
            'autosize': True,
            'vis': False,
            'x': -800,
            'y': 0,
            'tab_stop': False,
        })
        w = int(_get(h, name).get('w') or 0)
        if w <= 0:
            _set(h, name, vis=True)
            w = int(_get(h, name).get('w') or 0)
        return w if w > 0 else 0
    except Exception:
        return 0
    finally:
        try:
            dlg_proc(h, DLG_CTL_DELETE, name=name)
        except Exception:
            pass


def _apply_nav_width(h, names):
    text_w = 0
    for cap in names:
        text_w = max(text_w, _measure_caption(h, cap))
    if text_w <= 0:
        text_w = max((len(cap) for cap in names), default=0) * _EMU_CHAR
    _set(h, 'nav', w=nav_width(text_w))


def _add(h, kind, prop):
    n = dlg_proc(h, DLG_CTL_ADD, kind)
    dlg_proc(h, DLG_CTL_PROP_SET, index=n, prop=prop)
    return n


def _get(h, name):
    return dlg_proc(h, DLG_CTL_PROP_GET, name=name) or {}


def _set(h, name, **prop):
    dlg_proc(h, DLG_CTL_PROP_SET, name=name, prop=prop)


def _show_page(index):
    for i, name in enumerate(PAGES):
        _set(_h, 'page_' + name.lower(), vis=(i == index))


def _read_int(h, name, fallback=0):
    raw = _get(h, name).get('val')
    try:
        return int(str(raw if raw is not None else fallback))
    except (TypeError, ValueError):
        return fallback


def _snapshot_prefs():
    """Chrome + send/host values as they were when Config opened."""
    return {
        'exe': prefs.get_exe(),
        'collapse': prefs.get_collapse(),
        'keep_focus': prefs.get_keep_focus(),
        'source_echo': prefs.get_source_echo(),
        'source_encoding': prefs.get_source_encoding(),
        'pipe': prefs.get_pipe_token(),
        'icons_fg': prefs.get_icons_fg(),
        'grid_label': prefs.get_grid_label(),
        'show': prefs.get_chrome_show(),
    }


def _restore_prefs(snap):
    if not snap:
        return
    prefs.set_exe(snap.get('exe') or '')
    prefs.set_collapse(snap.get('collapse'))
    prefs.set_keep_focus(snap.get('keep_focus'))
    prefs.set_source_echo(snap.get('source_echo'))
    prefs.set_source_encoding(snap.get('source_encoding'))
    pipe = snap.get('pipe') or '|>'
    prefs.set_pipe_token('magrittr' if pipe == '%>%' else 'native')
    prefs.set_icons_fg(snap.get('icons_fg'))
    prefs.set_grid_label(snap.get('grid_label'))
    prefs.set_chrome_show(snap.get('show'))


def _rebuild_live():
    """Apply chrome now — Config stays open (modal)."""
    try:
        from . import chrome
    except ImportError:
        import chrome
    try:
        chrome.get().rebuild_chrome()
    except Exception:
        pass


def on_dlg(id_dlg, info):
    """String-callback hub (`Command.config_dlg`)."""
    global _saved, _applied
    if id_dlg != _h or not _h:
        return
    kind = (info or '').strip().lower()
    if kind == 'tree':
        hid = tree_proc(_h_tree, TREE_ITEM_GET_SELECTED)
        if not hid:
            return
        if hid in _items:
            idx = _items.index(hid)
        else:
            props = tree_proc(_h_tree, TREE_ITEM_GET_PROPS, id_item=hid) or {}
            try:
                idx = int(str(props.get('data') or '0'))
            except ValueError:
                idx = 0
        if idx < 0 or idx >= len(PAGES):
            idx = 0
        _show_page(idx)
        return
    if kind == 'all':
        show_on = {key: True for key, _c in _SHOW_DEFS}
        _set(
            _h, 'chrome_list',
            val=chrome_show.encode_checklist(show_on, _SHOW_KEYS),
        )
        return
    if kind == 'none':
        show_on = {key: False for key, _c in _SHOW_DEFS}
        _set(
            _h, 'chrome_list',
            val=chrome_show.encode_checklist(show_on, _SHOW_KEYS),
        )
        return
    if kind == 'browse':
        path = str(_get(_h, 'exe').get('val') or '').strip()
        init_dir = os.path.dirname(path) if path else ''
        init_name = os.path.basename(path) if path else host.exe_name()
        filt = 'STATghost|' + host.exe_name() + '|All|*'
        picked = dlg_file(
            True, init_name, init_dir, filt, 'STATghost executable',
        )
        if picked:
            _set(_h, 'exe', val=picked)
        return
    if kind == 'apply':
        if not _commit(id_dlg):
            return
        _applied = True
        _rebuild_live()
        return
    if kind == 'ok':
        if not _commit(id_dlg):
            return
        _saved = True
        dlg_proc(id_dlg, DLG_HIDE)
        return
    if kind == 'cancel':
        if _applied:
            _restore_prefs(_snapshot)
            _rebuild_live()
        _saved = False
        dlg_proc(id_dlg, DLG_HIDE)


def _memo_flat(h, name):
    """Memo val is TAB-separated lines; a path must stay one line."""
    raw = str(_get(h, name).get('val') or '')
    return raw.replace('\t', '').replace('\r', '').replace('\n', '').strip()


def _commit(h):
    path = _memo_flat(h, 'exe')
    if path and (not os.path.isfile(path)):
        msg_status(PLUGIN + ': file not found — ' + path)
        _show_page(PAGES.index('Host'))
        tree_proc(_h_tree, TREE_ITEM_SELECT, _items[PAGES.index('Host')])
        return False
    enc_idx = _read_int(h, 'enc', 0)
    if enc_idx < 0 or enc_idx >= len(_encs):
        enc_idx = _enc_index(_encs, 'utf-8')
    pipe_idx = _read_int(h, 'pipe', 0)
    if pipe_idx not in (0, 1):
        pipe_idx = 0
    icons_idx = _read_int(h, 'icons_fg', 0)
    if icons_idx < 0 or icons_idx >= len(_ICONS_FG_KEYS):
        icons_idx = 0
    grid_idx = _read_int(h, 'grid_label', 0)
    if grid_idx < 0 or grid_idx >= len(_GRID_LABEL_KEYS):
        grid_idx = 0
    collapse = _as_bool(_get(h, 'collapse').get('val'))
    keep_focus = _as_bool(_get(h, 'keep_focus').get('val'))
    src_echo = _as_bool(_get(h, 'src_echo').get('val'))
    show_on = chrome_show.decode_checklist(
        _get(h, 'chrome_list').get('val'),
        _SHOW_KEYS,
        fallback=_show_dict_from_prefs(),
    )
    chosen = [key for key, _c in _SHOW_DEFS if show_on.get(key)]
    if not chosen:
        chosen = list(chrome_show.DEFAULT_SHOW)
        msg_status(PLUGIN + ': no buttons selected — restored defaults')
    prefs.set_exe(path)
    prefs.set_collapse(collapse)
    prefs.set_keep_focus(keep_focus)
    prefs.set_source_echo(src_echo)
    prefs.set_source_encoding(_encs[enc_idx])
    prefs.set_pipe_token('magrittr' if pipe_idx == 1 else 'native')
    prefs.set_icons_fg(_ICONS_FG_KEYS[icons_idx])
    prefs.set_grid_label(_GRID_LABEL_KEYS[grid_idx])
    prefs.set_chrome_show(chosen)
    msg_status(
        PLUGIN + ': settings saved — buttons '
        + ','.join(prefs.get_chrome_show())
        + ', icons FG '
        + prefs.get_icons_fg()
        + ', grid '
        + prefs.get_grid_label()
    )
    return True


def _fill_send(h, collapse, keep_focus, src_echo, enc_idx, pipe_idx):
    stretch = {'a_r': ('', ']'), 'sp_r': 12}
    _add(h, 'label', {
        'name': 'send_head', 'p': 'page_send',
        'cap': 'How the plugin shapes EVAL / Source file.',
        'x': 12, 'y': 12, 'w': 200, 'h': 22, **stretch,
    })
    _add(h, 'check', {
        'name': 'keep_focus', 'p': 'page_send',
        'cap': 'Keep editor focused after Send',
        'val': '1' if keep_focus else '0',
        'x': 12, 'y': 44, 'w': 200, 'h': 26, **stretch,
    })
    # label ex0 = right-align (clips "Sniper" to "niper"). Memo ex3 wraps.
    _add(h, 'memo', {
        'name': 'keep_hint', 'p': 'page_send',
        'val': (
            'Asks STATghost to return to CudaText for this eval.\t'
            'Sniper inside STATghost still uses Settings → Behavior → '
            'Focus after eval.'
        ),
        'x': 12, 'y': 72, 'w': 200, 'h': 56, **stretch,
        'ex0': True,
        'ex1': False,
        'ex2': False,
        'ex3': True,
        'tab_stop': False,
    })
    _add(h, 'check', {
        'name': 'collapse', 'p': 'page_send',
        'cap': 'Send wraps as one Console line',
        'val': '1' if collapse else '0',
        'x': 12, 'y': 140, 'w': 200, 'h': 26, **stretch,
    })
    _add(h, 'check', {
        'name': 'src_echo', 'p': 'page_send',
        'cap': 'Source file: echo = TRUE',
        'val': '1' if src_echo else '0',
        'x': 12, 'y': 172, 'w': 200, 'h': 26, **stretch,
    })
    _add(h, 'label', {
        'name': 'enc_lbl', 'p': 'page_send',
        'cap': 'Source file encoding',
        'x': 12, 'y': 214, 'w': 200, 'h': 22,
    })
    _add(h, 'combo_ro', {
        'name': 'enc', 'p': 'page_send',
        'items': '\t'.join(_encs),
        'val': str(enc_idx),
        'x': 220, 'y': 210, 'w': 160, 'h': 28, **stretch,
    })
    _add(h, 'label', {
        'name': 'pipe_lbl', 'p': 'page_send',
        'cap': 'Insert pipe (Ctrl+Shift+M)',
        'x': 12, 'y': 256, 'w': 200, 'h': 22,
    })
    _add(h, 'combo_ro', {
        'name': 'pipe', 'p': 'page_send',
        'items': '\t'.join(_PIPE_ITEMS),
        'val': str(pipe_idx),
        'x': 220, 'y': 252, 'w': 160, 'h': 28, **stretch,
    })


def _fill_chrome(h, icons_idx, grid_idx, show_on):
    list_caps = '\t'.join(cap for _k, cap in _SHOW_DEFS)
    stretch = {'a_r': ('', ']'), 'sp_r': 12}
    _add(h, 'panel', {
        'name': 'chrome_head', 'p': 'page_chrome',
        'align': ALIGN_TOP, 'h': 40,
    })
    _add(h, 'panel', {
        'name': 'chrome_grid', 'p': 'page_chrome',
        'align': ALIGN_TOP, 'h': 40,
    })
    _add(h, 'panel', {
        'name': 'chrome_list_cap', 'p': 'page_chrome',
        'align': ALIGN_TOP, 'h': 28,
    })
    _add(h, 'panel', {
        'name': 'chrome_foot', 'p': 'page_chrome',
        'align': ALIGN_BOTTOM, 'h': 72,
    })
    _add(h, 'label', {
        'name': 'icons_lbl', 'p': 'chrome_head',
        'cap': 'Toolbar / side icons FG',
        'x': 12, 'y': 10, 'w': 200, 'h': 22,
    })
    _add(h, 'combo_ro', {
        'name': 'icons_fg', 'p': 'chrome_head',
        'items': '\t'.join(_ICONS_FG_ITEMS),
        'val': str(icons_idx),
        'x': 220, 'y': 6, 'w': 160, 'h': 28, **stretch,
    })
    _add(h, 'label', {
        'name': 'grid_lbl', 'p': 'chrome_grid',
        'cap': 'Side keypad labels',
        'x': 12, 'y': 10, 'w': 200, 'h': 22,
    })
    _add(h, 'combo_ro', {
        'name': 'grid_label', 'p': 'chrome_grid',
        'items': '\t'.join(_GRID_LABEL_ITEMS),
        'val': str(grid_idx),
        'x': 220, 'y': 6, 'w': 160, 'h': 28, **stretch,
    })
    _add(h, 'label', {
        'name': 'list_lbl', 'p': 'chrome_list_cap',
        'cap': 'Toolbar / side buttons (same nest tree)',
        'x': 12, 'y': 4, 'w': 200, 'h': 22, **stretch,
    })
    _add(h, 'checklistbox', {
        'name': 'chrome_list', 'p': 'page_chrome',
        'items': list_caps,
        'val': chrome_show.encode_checklist(show_on, _SHOW_KEYS),
        'align': ALIGN_CLIENT,
        'sp_l': 12, 'sp_r': 12, 'sp_t': 4, 'sp_b': 4,
    })
    _add(h, 'button', {
        'name': 'btn_none', 'p': 'chrome_foot',
        'cap': 'None',
        'w': 88, 'h': 28, 'y': 8,
        'a_l': None, 'a_t': None,
        'a_r': ('', ']'), 'a_b': None,
        'sp_r': 12,
        'on_change': _CB % 'none',
    })
    _add(h, 'button', {
        'name': 'btn_all', 'p': 'chrome_foot',
        'cap': 'All',
        'w': 88, 'h': 28, 'y': 8,
        'a_l': None, 'a_t': None,
        'a_r': ('btn_none', '['), 'a_b': None,
        'sp_r': 8,
        'on_change': _CB % 'all',
    })
    _add(h, 'label', {
        'name': 'chrome_hint', 'p': 'chrome_foot',
        'cap': 'Hidden actions stay in Plugins → STATghost.',
        'x': 12, 'y': 40, 'w': 200, 'h': 22, **stretch,
    })


def _fill_host(h, path, det_cap):
    stretch = {'a_r': ('', ']'), 'sp_r': 12}
    _add(h, 'panel', {
        'name': 'host_exe', 'p': 'page_host',
        'align': ALIGN_TOP, 'h': 118,
    })
    _add(h, 'panel', {
        'name': 'host_det', 'p': 'page_host',
        'align': ALIGN_TOP, 'h': 92,
    })
    _add(h, 'label', {
        'name': 'exe_lbl', 'p': 'host_exe',
        'cap': 'STATghost executable',
        'x': 12, 'y': 8, 'w': 200, 'h': 22, **stretch,
    })
    _add(h, 'button', {
        'name': 'btn_browse', 'p': 'host_exe',
        'cap': 'Browse…',
        'w': 96, 'h': 28, 'y': 36,
        'a_l': None, 'a_t': None,
        'a_r': ('', ']'), 'a_b': None,
        'sp_r': 12,
        'on_change': _CB % 'browse',
    })
    _add(h, 'memo', {
        'name': 'exe', 'p': 'host_exe',
        'val': path,
        'x': 12, 'y': 32, 'w': 200, 'h': 52,
        'a_r': ('btn_browse', '['), 'sp_r': 8,
        'ex0': False,
        'ex1': False,
        'ex2': True,
        'ex3': True,
    })
    _add(h, 'label', {
        'name': 'exe_hint', 'p': 'host_exe',
        'cap': 'Empty = auto-detect (sibling clone, then PATH).',
        'x': 12, 'y': 90, 'w': 200, 'h': 22, **stretch,
    })
    _add(h, 'label', {
        'name': 'det_lbl', 'p': 'host_det',
        'cap': 'Detected',
        'x': 12, 'y': 8, 'w': 200, 'h': 22, **stretch,
    })
    _add(h, 'memo', {
        'name': 'detected', 'p': 'host_det',
        'val': det_cap,
        'x': 12, 'y': 32, 'w': 200, 'h': 52, **stretch,
        'ex0': True,
        'ex1': False,
        'ex2': True,
        'ex3': True,
        'tab_stop': False,
    })


def show_config():
    global _h, _h_tree, _items, _saved, _applied, _snapshot, _encs
    path = prefs.get_exe() or host.find_exe(ignore_ini=True) or ''
    collapse = prefs.get_collapse()
    keep_focus = prefs.get_keep_focus()
    src_echo = prefs.get_source_echo()
    encoding = prefs.get_source_encoding()
    _encs = _cuda_encodings()
    enc_idx = _enc_index(_encs, encoding)
    pipe_idx = _pipe_index()
    icons_idx = _icons_fg_index()
    grid_idx = _grid_label_index()
    show_on = _show_dict_from_prefs()
    detected = host.find_exe(ignore_ini=True) or ''
    det_cap = detected if detected else '(not found)'
    _saved = False
    _applied = False
    _snapshot = _snapshot_prefs()
    _items = []

    h = dlg_proc(0, DLG_CREATE)
    _h = h
    dlg_proc(h, DLG_PROP_SET, prop={
        'cap': PLUGIN + ' plugin',
        'w': _W,
        'h': _H,
        'w_min': 560,
        'h_min': 360,
        'border': DBORDER_SIZE,
    })
    _add(h, 'panel', {
        'name': 'foot',
        'align': ALIGN_BOTTOM,
        'h': _FOOT,
    })
    _add(h, 'button', {
        'name': 'btn_cancel', 'p': 'foot',
        'cap': 'Cancel',
        'ex0': True,
        'w': 96, 'h': 28, 'y': 10,
        'a_l': None, 'a_t': None,
        'a_r': ('', ']'), 'a_b': None,
        'sp_r': 12,
        'on_change': _CB % 'cancel',
    })
    _add(h, 'button', {
        'name': 'btn_ok', 'p': 'foot',
        'cap': 'OK',
        'w': 96, 'h': 28, 'y': 10,
        'a_l': None, 'a_t': None,
        'a_r': ('btn_cancel', '['), 'a_b': None,
        'sp_r': 8,
        'on_change': _CB % 'ok',
    })
    _add(h, 'button', {
        'name': 'btn_apply', 'p': 'foot',
        'cap': 'Apply',
        'w': 96, 'h': 28, 'y': 10,
        'a_l': None, 'a_t': None,
        'a_r': ('btn_ok', '['), 'a_b': None,
        'sp_r': 8,
        'on_change': _CB % 'apply',
    })
    _add(h, 'treeview', {
        'name': 'nav',
        'align': ALIGN_LEFT,
        'w': _TREE_MIN,
        'sp_l': 8, 'sp_t': 8, 'sp_b': 8,
        'on_change': _CB % 'tree',
        'act': True,
        'tab_stop': False,
    })
    _h_tree = dlg_proc(h, DLG_CTL_HANDLE, name='nav')
    _add(h, 'panel', {
        'name': 'body',
        'align': ALIGN_CLIENT,
        'sp_l': 8, 'sp_t': 8, 'sp_r': 8, 'sp_b': 8,
    })
    for i, name in enumerate(PAGES):
        key = 'page_' + name.lower()
        _add(h, 'panel', {
            'name': key, 'p': 'body',
            'align': ALIGN_CLIENT,
            'vis': (i == 0),
        })
    _fill_send(h, collapse, keep_focus, src_echo, enc_idx, pipe_idx)
    _fill_chrome(h, icons_idx, grid_idx, show_on)
    _fill_host(h, path, det_cap)

    tree_proc(_h_tree, TREE_PROP_SHOW_ROOT, text='0')
    for i, name in enumerate(PAGES):
        hid = tree_proc(
            _h_tree, TREE_ITEM_ADD, 0, -1, name, -1, str(i),
        )
        _items.append(hid)
    if _items:
        tree_proc(_h_tree, TREE_ITEM_SELECT, _items[0])
    _apply_nav_width(h, PAGES)

    dlg_proc(h, DLG_SCALE)
    try:
        tree_proc(_h_tree, TREE_THEME)
    except Exception:
        pass
    dlg_proc(h, DLG_CTL_FOCUS, name='btn_cancel')
    dlg_proc(h, DLG_SHOW_MODAL)
    dlg_proc(h, DLG_FREE)
    _h = 0
    _h_tree = 0
    _items = []
    _snapshot = None
    return bool(_saved)
