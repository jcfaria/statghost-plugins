# Shared plugin prefs (cuda_statghost.ini). Lives in CudaText settings/.
# Not STATghost Console chrome. [bar] vis is leftover from the retired strip.

from __future__ import annotations

import os

from cudatext import APP_DIR_SETTINGS
from cudatext import app_path
from cudatext import ini_read
from cudatext import ini_write

INI_NAME = 'cuda_statghost.ini'

# In-process cache — INI is source of truth on disk; cache avoids a stale
# read if the editor keeps an old handle, and makes Send see OK immediately.
_collapse_cache = None
_keep_focus_cache = None
_source_echo_cache = None
_source_encoding_cache = None
_pipe_cache = None
_icons_fg_cache = None
_chrome_show_cache = None
_grid_label_cache = None


def ini_path():
    return os.path.join(app_path(APP_DIR_SETTINGS), INI_NAME)


def get_exe():
    return (ini_read(ini_path(), 'host', 'exe', '') or '').strip()


def set_exe(path):
    ini_write(ini_path(), 'host', 'exe', (path or '').strip())


def get_collapse():
    """Default on: send editor wraps as one Console line."""
    global _collapse_cache
    if _collapse_cache is not None:
        return bool(_collapse_cache)
    raw = ini_read(ini_path(), 'send', 'collapse', '1')
    if raw is None or str(raw).strip() == '':
        raw = '1'
    _collapse_cache = str(raw).strip() == '1'
    return bool(_collapse_cache)


def set_collapse(on):
    global _collapse_cache
    _collapse_cache = bool(on)
    ini_write(ini_path(), 'send', 'collapse', '1' if on else '0')


def get_keep_focus():
    """Default on: plugin Send asks STATghost to restore the editor."""
    global _keep_focus_cache
    if _keep_focus_cache is not None:
        return bool(_keep_focus_cache)
    raw = ini_read(ini_path(), 'send', 'keep_focus', '1')
    if raw is None or str(raw).strip() == '':
        raw = '1'
    _keep_focus_cache = str(raw).strip() == '1'
    return bool(_keep_focus_cache)


def set_keep_focus(on):
    global _keep_focus_cache
    _keep_focus_cache = bool(on)
    ini_write(ini_path(), 'send', 'keep_focus', '1' if on else '0')


def get_source_echo():
    """Default on: source(.path, echo=TRUE, …) for Source file."""
    global _source_echo_cache
    if _source_echo_cache is not None:
        return bool(_source_echo_cache)
    raw = ini_read(ini_path(), 'send', 'source_echo', '1')
    if raw is None or str(raw).strip() == '':
        raw = '1'
    _source_echo_cache = str(raw).strip() == '1'
    return bool(_source_echo_cache)


def set_source_echo(on):
    global _source_echo_cache
    _source_echo_cache = bool(on)
    ini_write(ini_path(), 'send', 'source_echo', '1' if on else '0')


def get_source_encoding():
    """Default UTF-8 — matches STATghost R EvalCode encoding."""
    global _source_encoding_cache
    if _source_encoding_cache is not None:
        return str(_source_encoding_cache)
    raw = ini_read(ini_path(), 'send', 'source_encoding', 'UTF-8')
    if raw is None or str(raw).strip() == '':
        raw = 'UTF-8'
    _source_encoding_cache = str(raw).strip()
    return str(_source_encoding_cache)


def set_source_encoding(enc):
    global _source_encoding_cache
    e = (enc or '').strip() or 'UTF-8'
    _source_encoding_cache = e
    ini_write(ini_path(), 'send', 'source_encoding', e)


def get_pipe_token():
    """Default native R pipe `|>` (R 4.1+); magrittr via Config."""
    global _pipe_cache
    if _pipe_cache is not None:
        return str(_pipe_cache)
    raw = ini_read(ini_path(), 'edit', 'pipe', 'native')
    if raw is None or str(raw).strip() == '':
        raw = 'native'
    key = str(raw).strip().lower()
    if key in ('magrittr', '%>%', 'tee'):
        _pipe_cache = '%>%'
    else:
        _pipe_cache = '|>'
    return str(_pipe_cache)


def set_pipe_token(kind):
    """kind: 'native' | 'magrittr' (or the tokens themselves)."""
    global _pipe_cache
    key = (kind or '').strip().lower()
    if key in ('magrittr', '%>%', 'tee'):
        ini_write(ini_path(), 'edit', 'pipe', 'magrittr')
        _pipe_cache = '%>%'
    else:
        ini_write(ini_path(), 'edit', 'pipe', 'native')
        _pipe_cache = '|>'


def get_icons_fg():
    """Icon FG: auto | light (white) | dark (graphite) | gray | theme."""
    global _icons_fg_cache
    if _icons_fg_cache is not None:
        return str(_icons_fg_cache)
    raw = ini_read(ini_path(), 'icons', 'fg', 'auto')
    if raw is None or str(raw).strip() == '':
        raw = 'auto'
    key = str(raw).strip().lower()
    if key not in ('auto', 'light', 'dark', 'gray', 'theme'):
        key = 'auto'
    _icons_fg_cache = key
    return str(_icons_fg_cache)


def set_icons_fg(mode):
    """mode: auto | light | dark | gray | theme."""
    global _icons_fg_cache
    key = (mode or '').strip().lower()
    if key not in ('auto', 'light', 'dark', 'gray', 'theme'):
        key = 'auto'
    ini_write(ini_path(), 'icons', 'fg', key)
    _icons_fg_cache = key


def get_chrome_show():
    """Which control-deck buttons are visible (toolbar + side, same set)."""
    global _chrome_show_cache
    if _chrome_show_cache is not None:
        return tuple(_chrome_show_cache)
    try:
        from . import chrome_show as cs
    except ImportError:
        import chrome_show as cs
    raw = ini_read(ini_path(), 'chrome', 'show', '')
    keys = cs.parse_show(raw)
    _chrome_show_cache = keys
    return tuple(_chrome_show_cache)


def set_chrome_show(keys):
    """Persist visible action ids (cores + Send/Source nest extras)."""
    global _chrome_show_cache
    try:
        from . import chrome_show as cs
    except ImportError:
        import chrome_show as cs
    keys = cs.parse_show(','.join(keys or ()))
    ini_write(ini_path(), 'chrome', 'show', cs.format_show(keys))
    _chrome_show_cache = keys


def get_grid_label():
    """Keypad caption: below (default) | icon."""
    global _grid_label_cache
    if _grid_label_cache is not None:
        return str(_grid_label_cache)
    try:
        from . import chrome_show as cs
    except ImportError:
        import chrome_show as cs
    raw = ini_read(ini_path(), 'chrome', 'grid_label', cs.GRID_LABEL_DEFAULT)
    _grid_label_cache = cs.parse_grid_label(raw)
    return str(_grid_label_cache)


def set_grid_label(mode):
    """mode: below | icon."""
    global _grid_label_cache
    try:
        from . import chrome_show as cs
    except ImportError:
        import chrome_show as cs
    key = cs.parse_grid_label(mode)
    ini_write(ini_path(), 'chrome', 'grid_label', key)
    _grid_label_cache = key


def encoding_for_r(enc=None):
    """Map CudaText / prefs name to what R `source(..., encoding=)` expects."""
    if enc is None:
        enc = get_source_encoding()
    n = (enc or '').strip()
    if not n:
        return 'UTF-8'
    key = n.lower().replace('_', '-')
    if key in ('utf-8', 'utf8', 'utf-8 bom', 'utf8 bom', 'utf-8 with bom'):
        return 'UTF-8'
    if key in ('latin1', 'latin-1', 'iso-8859-1'):
        return 'latin1'
    if key in ('utf-16 le', 'utf-16le', 'utf16le'):
        return 'UTF-16LE'
    if key in ('utf-16 be', 'utf-16be', 'utf16be'):
        return 'UTF-16BE'
    return n
