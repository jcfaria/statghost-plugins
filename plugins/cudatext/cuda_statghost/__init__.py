# STATghost CudaText plugin — VP-EB-1 send-to-sniper (layer A).
# Transport = system clipboard UTF-8 (layer B). No REPL inside CudaText.
# Command class stays thin: new actions = method + install.inf.
# Native chrome (VP-EB-1b) = chrome.py — main toolbar + side tab.

import os

from cudatext import APPSTATE_THEME_UI
from cudatext import DMENU_LIST
from cudatext import app_proc, PROC_SET_CLIP
from cudatext import dlg_menu
from cudatext import ed
from cudatext import msg_status

try:
    from . import chrome
    from . import chrome_show
    from . import clip as sgclip
    from . import config as plugincfg
    from . import editor
    from . import host
    from . import outline as sgoutline
    from . import paths as sgpaths
    from . import prefs
    from . import protocol
    from . import ranges as sgranges
    from . import rword
    from .statement import (
        collapse_wraps,
        dedent_block,
        enclosing_function,
        extend_statement,
        join_lines,
    )
except ImportError:
    import chrome
    import chrome_show
    import clip as sgclip
    import config as plugincfg
    import editor
    import host
    import outline as sgoutline
    import paths as sgpaths
    import prefs
    import protocol
    import ranges as sgranges
    import rword
    from statement import (
        collapse_wraps,
        dedent_block,
        enclosing_function,
        extend_statement,
        join_lines,
    )

PLUGIN = 'STATghost'


def _set_clip(text):
    """Native clipboard + X11 + Wayland so gtk2/Qt6 hosts reach any SG."""
    sgclip.push(text, native=lambda t: app_proc(PROC_SET_CLIP, t))


def _line_count(text):
    if text is None or text == '':
        return 0
    t = text.replace('\r\n', '\n').replace('\r', '\n')
    return t.count('\n') + 1


def _r_quote(path):
    """R double-quoted path; prefer / separators (works on Win + Unix)."""
    s = (path or '').replace('\\', '/')
    return '"' + s.replace('"', '\\"') + '"'


def _send_code(text, mode, apply_collapse=True):
    """Student chunk — STATghost evals only when Armed.

    Collapse is plugin-side shaping of the EVAL body. STATghost then
    echoes 1 line as `>` and 2+ as original wraps (`>` / `+`) — so
    collapse OFF is what the student typed; collapse ON is one line.
    """
    if text is None or text.strip() == '':
        msg_status(PLUGIN + ': nothing to send (' + mode + ')')
        return False
    text = dedent_block(text)
    n_in = _line_count(text)
    collapse = prefs.get_collapse() if apply_collapse else False
    if collapse:
        text = collapse_wraps(text)
    n_out = _line_count(text)
    _set_clip(protocol.make_eval(text, keep_focus=prefs.get_keep_focus()))
    msg_status(
        PLUGIN + ': sent ' + mode + ' (' + str(len(text))
        + ' chars, lines ' + str(n_in) + '→' + str(n_out)
        + ', collapse '
        + ('ON' if collapse else 'OFF')
        + ') — STATghost must be Armed'
    )
    return True


def _send_command(name, hint):
    """Control token — STATghost handles Idle or Armed; never evals it."""
    _set_clip(protocol.make_command(name))
    msg_status(PLUGIN + ': ' + hint)
    return True


def _statement_at_caret():
    """Prefer enclosing function (caret anywhere in body), else one statement."""
    y0 = editor.caret_line_index()
    if y0 is None:
        return None, None, '', 'statement'
    n = editor.line_count()
    fs, fe = enclosing_function(y0, editor.get_line, n)
    if fs is not None and fe is not None:
        text = join_lines(editor.get_line, fs, fe)
        return fs, fe, text, 'function'
    y = editor.skip_to_code_line(y0)
    if y is None:
        return None, None, '', 'statement'
    start, end = extend_statement(y, editor.get_line, n)
    text = join_lines(editor.get_line, start, end)
    return start, end, text, 'statement'


def _build_source_slot_code(slot_1based):
    """source(.paths[n], …) — buffer already written to the shared slot."""
    echo = 'TRUE' if prefs.get_source_echo() else 'FALSE'
    enc = prefs.encoding_for_r()
    return (
        'source(.paths[' + str(int(slot_1based)) + '], echo = ' + echo
        + ', spaced = FALSE, encoding = ' + _r_quote(enc) + ')'
    )


def _insert_at_caret(text):
    carets = ed.get_carets()
    if not carets:
        return False
    x, y, _x2, _y2 = carets[0]
    if y < 0:
        return False
    ed.insert(x, y, text)
    ed.set_caret(x + len(text), y)
    return True


class Command:

    def send_selection(self):
        """Send selection; if empty, enclosing function or statement at caret.

        Function (RStudio-style): caret anywhere inside `f <- function() {…}`
        sends the whole definition, not only the inner line.
        """
        sel = editor.selection_text()
        if sel.strip() != '':
            last = editor.selection_last_line()
            if _send_code(sel, 'selection') and last is not None:
                editor.advance_caret_after(last)
            return
        _start, end, text, mode = _statement_at_caret()
        if _send_code(text, mode) and end is not None:
            editor.advance_caret_after(end)

    def send_function(self):
        """Send only the enclosing function at caret (no selection fallback)."""
        y = editor.caret_line_index()
        if y is None:
            msg_status(PLUGIN + ': nothing to send (function)')
            return
        n = editor.line_count()
        fs, fe = enclosing_function(y, editor.get_line, n)
        if fs is None or fe is None:
            msg_status(PLUGIN + ': caret not inside a function')
            return
        text = '\n'.join(editor.get_line(i) or '' for i in range(fs, fe + 1))
        if _send_code(text, 'function') and fe is not None:
            editor.advance_caret_after(fe)

    def send_above(self):
        """Send from start of file through caret line (RStudio Ctrl+Alt+B)."""
        y = editor.caret_line_index()
        if y is None:
            msg_status(PLUGIN + ': nothing to send (above)')
            return
        n = editor.line_count()
        text = sgranges.lines_from_start(editor.get_line, y, n)
        if _send_code(text, 'above'):
            editor.advance_caret_after(y)

    def send_below(self):
        """Send from caret line through EOF (RStudio Ctrl+Alt+E)."""
        y = editor.caret_line_index()
        if y is None:
            msg_status(PLUGIN + ': nothing to send (below)')
            return
        n = editor.line_count()
        text = sgranges.lines_to_end(editor.get_line, y, n)
        _send_code(text, 'below')

    def send_chunk(self):
        """Send blank/#-separated sniper chunk containing the caret."""
        y = editor.caret_line_index()
        if y is None:
            msg_status(PLUGIN + ': nothing to send (chunk)')
            return
        n = editor.line_count()
        start, end = sgranges.sniper_chunk_bounds(
            y, editor.get_line, n, editor.is_blank_or_hash_comment,
        )
        if start is None:
            msg_status(PLUGIN + ': nothing to send (chunk)')
            return
        text = sgranges.join_range(editor.get_line, start, end)
        if _send_code(text, 'chunk') and end is not None:
            editor.advance_caret_after(end)

    def send_file(self):
        """Whole buffer → TEMP/STATghost/file.R → source(.paths[4], …).

        TinnRcom pattern: shared `.paths` slot (STATghostcom), not an
        absolute editor path on the Console. Armed R + companion loaded.
        """
        text = ed.get_text_all()
        if text is None:
            text = ''
        try:
            sgpaths.write_slot(sgpaths.IDX_FILE, text)
        except OSError as e:
            msg_status(PLUGIN + ': cannot write .paths[4] — ' + str(e))
            return
        code = _build_source_slot_code(sgpaths.IDX_FILE)
        _send_code(code, 'source-file', apply_collapse=False)

    def source_selection(self):
        """Selection (or enclosing function) → .paths[5] → source(.paths[5])."""
        sel = editor.selection_text()
        if sel.strip() != '':
            text = sel
            mode = 'source-selection'
        else:
            _s, _e, text, mode0 = _statement_at_caret()
            mode = 'source-' + mode0
        if text is None or text.strip() == '':
            msg_status(PLUGIN + ': nothing to source')
            return
        text = dedent_block(text)
        try:
            sgpaths.write_slot(sgpaths.IDX_SELECTION, text)
        except OSError as e:
            msg_status(PLUGIN + ': cannot write .paths[5] — ' + str(e))
            return
        code = _build_source_slot_code(sgpaths.IDX_SELECTION)
        _send_code(code, mode, apply_collapse=False)

    def set_wd_here(self):
        """Send setwd() to the directory of the current file (R classroom)."""
        path = ed.get_filename() or ''
        if not path:
            msg_status(PLUGIN + ': save the file first (setwd)')
            return
        folder = os.path.dirname(os.path.realpath(path))
        if not folder:
            msg_status(PLUGIN + ': no directory for setwd')
            return
        _send_code('setwd(' + _r_quote(folder) + ')', 'setwd', apply_collapse=False)

    def inspect_print(self):
        """EVAL the identifier (or one-line selection) under the caret."""
        target = editor.r_print_target()
        if not target:
            msg_status(PLUGIN + ': no identifier to print')
            return
        _send_code(target, 'print', apply_collapse=False)

    def inspect_ls(self):
        _send_code('ls()', 'ls', apply_collapse=False)

    def inspect_str(self):
        self._inspect_wrap('str', 'str')

    def inspect_names(self):
        self._inspect_wrap('names', 'names')

    def inspect_plot(self):
        self._inspect_wrap('plot', 'plot')

    def inspect_head(self):
        self._inspect_wrap('head', 'head')

    def inspect_tail(self):
        self._inspect_wrap('tail', 'tail')

    def inspect_help(self):
        code = rword.help_code(editor.r_wrap_target())
        if not code:
            msg_status(PLUGIN + ': no identifier for help')
            return
        _send_code(code, 'help', apply_collapse=False)

    def _inspect_wrap(self, fn, mode):
        code = rword.wrap_code(fn, editor.r_wrap_target())
        if not code:
            msg_status(PLUGIN + ': no identifier for ' + mode)
            return
        _send_code(code, mode, apply_collapse=False)

    def inspect_graphics_off(self):
        _send_code('graphics.off()', 'graphics.off', apply_collapse=False)

    def inspect_rm_all(self):
        _send_code('rm(list=ls())', 'rm', apply_collapse=False)

    def inspect_clear_all(self):
        """Wipe Console, then EVAL rm + graphics.off (Tinn Clear all)."""
        if chrome.get(self).host_cmd_allowed():
            _send_command(
                protocol.CMD_CLEAR,
                'clear all: Console wipe, then workspace + graphics',
            )
            try:
                from cudatext import TIMER_START_ONE
                from cudatext import timer_proc
                timer_proc(
                    TIMER_START_ONE,
                    'cuda_statghost.clear_all_eval',
                    450,
                )
                return
            except Exception:
                pass
        _send_code(
            'rm(list=ls()); graphics.off()',
            'clear-all',
            apply_collapse=False,
        )

    def clear_all_eval(self, tag='', info=''):
        """Second tick of Clear all — workspace after the CLEAR clip."""
        _send_code(
            'rm(list=ls()); graphics.off()',
            'clear-all',
            apply_collapse=False,
        )

    def insert_assign(self):
        """Insert ` <- ` (RStudio Alt+-)."""
        if _insert_at_caret(' <- '):
            msg_status(PLUGIN + ': inserted <-')
        else:
            msg_status(PLUGIN + ': no caret')

    def insert_pipe(self):
        """Insert native ` |> ` or magrittr ` %>% ` (Config / prefs)."""
        tok = prefs.get_pipe_token()
        if _insert_at_caret(' ' + tok + ' '):
            msg_status(PLUGIN + ': inserted ' + tok)
        else:
            msg_status(PLUGIN + ': no caret')

    def show_outline(self):
        """Document outline — sections + functions (RStudio lite)."""
        n = editor.line_count()
        items = sgoutline.collect_outline(editor.get_line, n)
        if not items:
            msg_status(PLUGIN + ': outline empty')
            return
        caps = [sgoutline.format_caption(it) for it in items]
        res = dlg_menu(DMENU_LIST, '\n'.join(caps))
        if res is None:
            return
        try:
            idx = int(res)
        except (TypeError, ValueError):
            return
        if idx < 0 or idx >= len(items):
            return
        line = int(items[idx]['line'])
        ed.set_caret(0, line)
        msg_status(PLUGIN + ': outline → L' + str(line + 1))

    def outline_jump(self):
        """Side-tab double-click → jump (chrome keeps the index map)."""
        chrome.get(self).jump_outline_selection()

    def clear_console(self):
        """Ask STATghost to wipe Console text (Ctrl+L). Works Idle or Armed."""
        if not chrome.get(self).host_cmd_allowed():
            return
        _send_command(
            protocol.CMD_CLEAR,
            'clear Console requested — STATghost must be running',
        )

    def toggle_arm(self):
        """Idle→ARM or Armed→IDLE. Absolute tokens — TOGGLE inverts SG."""
        ch = chrome.get(self)
        cmd = protocol.next_arm_cmd(ch.is_armed())
        want = cmd == protocol.CMD_ARM
        _send_command(
            cmd,
            ('Arm' if want else 'Idle') + ' requested — STATghost must be running',
        )
        ch.note_arm_state(want)
        ch.refresh()

    def toggle_host(self):
        """Start STATghost if it is down; quit if it is up.

        Never from CudaText startup — only a conscious toolbar/menu click.
        """
        if not chrome.get(self).host_cmd_allowed():
            return
        if host.is_running():
            def _quit_clip():
                _set_clip(protocol.make_command(protocol.CMD_QUIT))

            ok, msg = host.stop_graceful(_quit_clip)
            if ok:
                msg_status(PLUGIN + ': ' + msg)
            chrome.get(self).note_host_down()
            chrome.get(self).refresh()
            return
        ok, msg = host.start()
        if ok:
            if msg == 'already running':
                msg_status(PLUGIN + ': already running — one instance')
            else:
                msg_status(PLUGIN + ': started ' + msg)
            chrome.get(self).note_host_up()
            chrome.get(self).refresh()
            return
        msg_status(PLUGIN + ': ' + msg)
        if plugincfg.show_config():
            ok, msg = host.start()
            if ok:
                if msg == 'already running':
                    msg_status(PLUGIN + ': already running — one instance')
                else:
                    msg_status(PLUGIN + ': started ' + msg)
                chrome.get(self).note_host_up()
            else:
                msg_status(PLUGIN + ': ' + msg)
        chrome.get(self).refresh()

    def config(self):
        """Plugin settings — exe / icons FG / visible chrome buttons."""
        if plugincfg.show_config():
            chrome.get(self).rebuild_chrome()
        else:
            chrome.get(self).refresh()

    def config_dlg(self, id_dlg, id_ctl, data='', info=''):
        """dlg_proc string callback (gtk2: bound methods do not fire)."""
        plugincfg.on_dlg(id_dlg, info or data)

    def open_side(self):
        """Sidebar button / Plugins → STATghost side tab."""
        chrome.get(self).open_side(activate=True, focus=True)

    def chrome_tick(self, tag='', info=''):
        chrome.get(self).tick(tag)

    def toggle_bar(self):
        """Retired experimental docked strip — point at native chrome."""
        msg_status(
            PLUGIN + ': docked bar retired — use the toolbar and the '
            'STATghost side tab'
        )

    def _(self):
        """Menu separator placeholder (install.inf)."""
        pass

    def on_start2(self, ed_self):
        chrome.get(self).on_start()

    def on_state(self, ed_self, state):
        if state == APPSTATE_THEME_UI:
            chrome.get(self).reload_icons()

    def on_cli(self, *args):
        """Lab / cyclic TF: `cudatext -p=cuda_statghost#inspect_ls`."""
        name = ''
        for a in args:
            if isinstance(a, str) and a.strip() in chrome_show.CLI_METHODS:
                name = a.strip()
                break
        if not name:
            msg_status(PLUGIN + ': on_cli ignored')
            return
        fn = getattr(self, name, None)
        if not callable(fn):
            msg_status(PLUGIN + ': on_cli missing ' + name)
            return
        fn()
