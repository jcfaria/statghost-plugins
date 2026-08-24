#!/usr/bin/env python3
# Automated unit checks for cuda_statghost (no CudaText host required).
# Run: python3 test_unit.py

from __future__ import annotations

import ast
import os
import re
import subprocess
import sys
import tempfile
import unittest

# Allow `python3 test_unit.py` from this folder or repo root.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import paths  # noqa: E402
import protocol  # noqa: E402
import statement  # noqa: E402
import icons_fg  # noqa: E402
import chrome_show  # noqa: E402
import outline  # noqa: E402
import ranges  # noqa: E402
import rword  # noqa: E402
import host  # noqa: E402


def _lines(text):
    rows = text.replace('\r\n', '\n').replace('\r', '\n').split('\n')
    return rows


def _get(rows):
    def get_line(i):
        if i < 0 or i >= len(rows):
            return ''
        return rows[i]
    return get_line


class TestCollapseWraps(unittest.TestCase):
    def test_trailing_paren_joins(self):
        src = 'plot(\n  x\n)'
        out = statement.collapse_wraps(src)
        self.assertEqual(out.count('\n'), 0)
        self.assertIn('plot(', out)
        self.assertTrue(out.rstrip().endswith(')'))

    def test_operator_join(self):
        src = 'a <- 1 +\n  2'
        out = statement.collapse_wraps(src)
        self.assertEqual(out, 'a <- 1 + 2')

    def test_blank_chunk_cut(self):
        src = 'plot(x)\n\nabline(0, 1)'
        out = statement.collapse_wraps(src)
        self.assertEqual(out, src)

    def test_brace_block_keeps_statements(self):
        src = '''with(BOD, {
  plot(demand ~ Time,
       xlim = c(0, 8),
       ylim = c(0, 20),
       main = "sample 12 — BOD nls")
  points(predict(m_1) ~ Time,
         col = "red",
         pch = 19)
  lines(spline(predict(m_1) ~ Time, n = 200),
        col = "red",
        lwd = 2)
})'''
        out = statement.collapse_wraps(src)
        self.assertIn('\n', out)
        self.assertNotIn(') points', out)
        self.assertNotIn(') lines', out)
        self.assertIn('plot(demand ~ Time, xlim = c(0, 8)', out)
        self.assertIn('points(predict(m_1) ~ Time, col = "red", pch = 19)', out)
        self.assertTrue(out.rstrip().endswith('})'))

    def test_lone_close_paren_joins(self):
        src = 'plot(\n  x,\n  y\n)'
        out = statement.collapse_wraps(src)
        self.assertEqual(out, 'plot( x, y )')

    def test_deriv_wrap_joins_when_collapse_on(self):
        # Collapse ON: one Console line. Collapse OFF is identity in _send_code
        # (SG reprints wraps with `>`/`+`).
        src = 'deriv(fl,\n      c("a", "b"))'
        self.assertIn('\n', src)
        out = statement.collapse_wraps(src)
        self.assertEqual(out.count('\n'), 0)
        self.assertIn('deriv(fl,', out)
        self.assertIn('c("a", "b")', out)


class TestProtocol(unittest.TestCase):
    def test_eval_roundtrip(self):
        msg = protocol.make_eval('1 + 1')
        cmd, body = protocol.parse_message(msg)
        self.assertEqual(cmd, protocol.CMD_EVAL)
        self.assertEqual(body, '1 + 1')

    def test_eval_keep_roundtrip(self):
        msg = protocol.make_eval('1 + 1', keep_focus=True)
        cmd, body = protocol.parse_message(msg)
        self.assertEqual(cmd, protocol.CMD_EVAL_KEEP)
        self.assertEqual(body, '1 + 1')
        plain = protocol.make_eval('1 + 1')
        cmd, body = protocol.parse_message(plain)
        self.assertEqual(cmd, protocol.CMD_EVAL)
        self.assertEqual(body, '1 + 1')

    def test_clear_token(self):
        msg = protocol.make_command(protocol.CMD_CLEAR)
        cmd, body = protocol.parse_message(msg)
        self.assertEqual(cmd, protocol.CMD_CLEAR)
        self.assertEqual(body, '')

    def test_nonce_unique(self):
        a = protocol.make_command(protocol.CMD_ARM)
        b = protocol.make_command(protocol.CMD_ARM)
        self.assertNotEqual(a, b)

    def test_next_arm_cmd_absolute(self):
        self.assertEqual(protocol.next_arm_cmd(False), protocol.CMD_ARM)
        self.assertEqual(protocol.next_arm_cmd(True), protocol.CMD_IDLE)
        self.assertNotEqual(protocol.next_arm_cmd(False), protocol.CMD_TOGGLE_ARM)


class TestPaths(unittest.TestCase):
    def test_slot4_basename(self):
        p = paths.path_at(paths.IDX_FILE)
        self.assertTrue(p.endswith('file.R'))
        self.assertIn('STATghost', p)

    def test_write_slot_roundtrip(self):
        root = paths.paths_dir()
        os.makedirs(root, exist_ok=True)
        text = 'x <- 1\n'
        path = paths.write_slot(paths.IDX_FILE, text)
        with open(path, encoding='utf-8') as f:
            self.assertEqual(f.read(), text)


class TestEnclosingFunction(unittest.TestCase):
    def test_r_caret_in_body(self):
        src = '''\
foo <- function(x) {
  y <- x + 1
  y
}
'''
        rows = _lines(src)
        # caret on "y <- x + 1"
        s, e = statement.enclosing_function(1, _get(rows), len(rows))
        self.assertEqual((s, e), (0, 3))
        text = statement.join_lines(_get(rows), s, e)
        self.assertIn('foo <- function', text)
        self.assertIn('y <- x + 1', text)

    def test_r_caret_on_closing_brace(self):
        src = '''\
foo <- function(x) {
  x
}
'''
        rows = _lines(src)
        s, e = statement.enclosing_function(2, _get(rows), len(rows))
        self.assertEqual((s, e), (0, 2))

    def test_r_nested_innermost(self):
        src = '''\
outer <- function(x) {
  inner <- function(y) {
    y + 1
  }
  inner(x)
}
'''
        rows = _lines(src)
        # inside inner body
        s, e = statement.enclosing_function(2, _get(rows), len(rows))
        self.assertEqual(s, 1)
        self.assertIn('inner <- function', rows[s])
        # on inner(x) — outside inner, inside outer
        s2, e2 = statement.enclosing_function(4, _get(rows), len(rows))
        self.assertEqual(s2, 0)
        self.assertIn('outer <- function', rows[s2])

    def test_r_equals_assign(self):
        src = '''\
f = function(a, b) {
  a + b
}
'''
        rows = _lines(src)
        s, e = statement.enclosing_function(1, _get(rows), len(rows))
        self.assertEqual(s, 0)

    def test_not_inside_function(self):
        src = 'x <- 1\ny <- 2\n'
        rows = _lines(src)
        s, e = statement.enclosing_function(1, _get(rows), len(rows))
        self.assertEqual((s, e), (None, None))

    def test_python_def(self):
        src = '''\
def foo(x):
    y = x + 1
    return y

z = 1
'''
        rows = _lines(src)
        s, e = statement.enclosing_function(1, _get(rows), len(rows))
        self.assertEqual(s, 0)
        self.assertEqual(e, 2)


class TestChromeShow(unittest.TestCase):
    def test_parse_default_and_order(self):
        self.assertEqual(chrome_show.parse_show(''), chrome_show.DEFAULT_SHOW)
        self.assertEqual(
            chrome_show.parse_show('clear,cfg,send'),
            ('cfg', 'send', 'clear'),
        )
        self.assertIn('function', chrome_show.ACTION_KEYS)

    def test_filter_keeps_mid_sep(self):
        tb = (
            ('sep', '-', None, None),
            ('cfg', 'c', 'config', 'a.png'),
            ('arm', 'a', 'toggle_arm', 'b.png'),
            ('sep_send', '-', None, None),
            ('send', 's', 'send_selection', 'c.png'),
            ('function', 'f', 'send_function', 'f.png'),
            ('clear', 'x', 'clear_console', 'd.png'),
            ('sep_edit', '-', None, None),
            ('outline', 'o', 'show_outline', 'o.png'),
        )
        rows = chrome_show.filter_toolbar_rows(tb, ('cfg', 'send', 'outline'))
        names = [r[0] for r in rows]
        self.assertEqual(
            names, ['sep', 'cfg', 'sep_send', 'send', 'sep_edit', 'outline'],
        )

    def test_filter_empty(self):
        tb = (
            ('sep', '-', None, None),
            ('cfg', 'c', 'config', 'a.png'),
        )
        self.assertEqual(chrome_show.filter_toolbar_rows(tb, ()), ())

    def test_nest_menu_keys_default(self):
        self.assertEqual(
            chrome_show.nest_menu_keys('send', chrome_show.DEFAULT_SHOW),
            ('function', 'above', 'below', 'chunk'),
        )
        self.assertEqual(
            chrome_show.nest_menu_keys('source', chrome_show.DEFAULT_SHOW),
            ('srcsel', 'setwd'),
        )
        self.assertEqual(
            chrome_show.nest_menu_keys('inspect', chrome_show.DEFAULT_SHOW),
            ('ls', 'str', 'names', 'plot', 'help', 'head', 'tail'),
        )
        self.assertEqual(
            chrome_show.nest_menu_keys('clear', chrome_show.DEFAULT_SHOW),
            ('close_graphics', 'remove_objects', 'clear_all'),
        )
        self.assertEqual(chrome_show.nest_menu_keys('cfg', chrome_show.DEFAULT_SHOW), ())

    def test_collapse_hides_children_when_parent_shown(self):
        tb = (
            ('sep', '-', None, None),
            ('cfg', 'c', 'config', 'a.png'),
            ('sep_send', '-', None, None),
            ('send', 's', 'send_selection', 's.png'),
            ('function', 'f', 'send_function', 'f.png'),
            ('chunk', 'k', 'send_chunk', 'k.png'),
            ('source', 'o', 'send_file', 'o.png'),
            ('srcsel', 'r', 'source_selection', 'r.png'),
            ('setwd', 'w', 'set_wd_here', 'w.png'),
            ('inspect', 'i', 'inspect_print', 'i.png'),
            ('ls', 'l', 'inspect_ls', 'l.png'),
            ('str', 't', 'inspect_str', 't.png'),
            ('clear', 'x', 'clear_console', 'x.png'),
            ('close_graphics', 'g', 'inspect_graphics_off', 'g.png'),
            ('clear_all', 'a', 'inspect_clear_all', 'a.png'),
        )
        rows = chrome_show.filter_toolbar_rows(tb, chrome_show.DEFAULT_SHOW)
        names = [r[0] for r in chrome_show.collapse_nested_rows(rows)]
        self.assertEqual(
            names,
            ['sep', 'cfg', 'sep_send', 'send', 'source', 'inspect', 'clear'],
        )
        self.assertNotIn('function', names)
        self.assertNotIn('setwd', names)
        self.assertNotIn('ls', names)
        self.assertNotIn('clear_all', names)

    def test_collapse_keeps_orphan_child(self):
        tb = (
            ('sep', '-', None, None),
            ('function', 'f', 'send_function', 'f.png'),
            ('clear', 'x', 'clear_console', 'x.png'),
        )
        rows = chrome_show.filter_toolbar_rows(tb, ('function', 'clear'))
        names = [r[0] for r in chrome_show.collapse_nested_rows(rows)]
        self.assertEqual(names, ['sep', 'function', 'clear'])

    def test_side_filter(self):
        side = (
            ('cfg', 'Config', 'config', 'a.png'),
            ('send', 'Send', 'send_selection', 'b.png'),
            ('function', 'Function', 'send_function', 'f.png'),
            ('clear', 'Clear', 'clear_console', 'c.png'),
        )
        out = chrome_show.filter_side_actions(side, ('send',))
        self.assertEqual([r[0] for r in out], ['send'])
        collapsed = chrome_show.filter_side_actions(
            side, ('send', 'function', 'clear'),
        )
        self.assertEqual([r[0] for r in collapsed], ['send', 'clear'])

    def test_side_keys_match_toolbar_order(self):
        keys = chrome_show.side_keys(chrome_show.DEFAULT_SHOW)
        self.assertEqual(
            keys,
            ('cfg', 'arm', 'host', 'send', 'source', 'inspect', 'clear'),
        )
        nested = chrome_show.collapse_nested_rows(
            tuple((k, k, k, 'x.png') for k in chrome_show.DEFAULT_SHOW),
        )
        top = tuple(r[0] for r in nested)
        self.assertEqual(keys, top)

    def test_grid_plan_all_actions_three_cols(self):
        plan = chrome_show.grid_plan()
        keys = []
        hdrs = []
        for kind, payload in plan:
            if kind == 'hdr':
                hdrs.append(payload)
                continue
            self.assertEqual(kind, 'row')
            self.assertGreaterEqual(len(payload), 1)
            self.assertLessEqual(len(payload), chrome_show.GRID_COLS)
            keys.extend(payload)
        self.assertEqual(tuple(keys), chrome_show.ACTION_KEYS)
        self.assertEqual(tuple(hdrs), chrome_show.GRID_GROUP_TITLES)
        send = ('send', 'function', 'above', 'below', 'chunk')
        self.assertIn(('hdr', 'Send'), plan)
        self.assertIn(('row', send[:3]), plan)
        self.assertIn(('row', send[3:]), plan)

    def test_grid_plan_filters_and_drops_empty_groups(self):
        plan = chrome_show.grid_plan(('send', 'function', 'clear'))
        self.assertEqual(
            plan,
            (
                ('hdr', 'Send'),
                ('row', ('send', 'function')),
                ('hdr', 'Clear'),
                ('row', ('clear',)),
            ),
        )
        self.assertEqual(chrome_show.grid_keys(), chrome_show.ACTION_KEYS)

    def test_grid_label_default_is_below(self):
        self.assertEqual(chrome_show.GRID_LABEL_DEFAULT, 'below')
        self.assertEqual(chrome_show.parse_grid_label(''), 'below')
        self.assertEqual(chrome_show.parse_grid_label(None), 'below')
        self.assertEqual(chrome_show.parse_grid_label('junk'), 'below')
        self.assertEqual(chrome_show.parse_grid_label('below'), 'below')
        self.assertEqual(chrome_show.parse_grid_label('icon'), 'icon')
        self.assertEqual(chrome_show.parse_grid_label('beside'), 'icon')
        self.assertEqual(chrome_show.parse_grid_label('under'), 'below')
        self.assertEqual(
            chrome_show.GRID_LABELS,
            ('below', 'icon'),
        )
        here = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(here, 'prefs.py'), encoding='utf-8') as fh:
            prefs_txt = fh.read()
        self.assertIn('def get_grid_label', prefs_txt)
        self.assertIn('def set_grid_label', prefs_txt)
        self.assertIn("'chrome', 'grid_label'", prefs_txt)
        self.assertIn('cs.GRID_LABEL_DEFAULT', prefs_txt)

    def test_grid_panel_min_w_locked_to_owner_lab(self):
        self.assertEqual(chrome_show.GRID_PANEL_MIN_W, 150)
        self.assertEqual(chrome_show.grid_panel_min_w(), 150)
        self.assertGreaterEqual(
            chrome_show.grid_panel_min_w(),
            chrome_show.GRID_COLS * chrome_show.grid_cell_w(),
        )
        here = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(here, 'prefs.py'), encoding='utf-8') as fh:
            prefs_txt = fh.read()
        self.assertIn('def get_grid_panel_min_w', prefs_txt)
        self.assertIn("'chrome', 'grid_panel_min_w'", prefs_txt)
        with open(os.path.join(here, 'chrome.py'), encoding='utf-8') as fh:
            chrome_txt = fh.read()
        size_fn = chrome_txt.split('def _size_side_grid', 1)[1].split(
            'def _fill_side_grid', 1,
        )[0]
        self.assertIn('_side_panel_min_w()', size_fn)
        self.assertIn("'w_min': min_w", size_fn)

    def test_grid_cell_w_is_longest_cap_plus_20pct(self):
        longest = max(len(c) for c in chrome_show.GRID_CAP.values())
        expect = max(
            chrome_show.GRID_CELL_MIN,
            int(round(longest * chrome_show.GRID_EMU_CHAR * chrome_show.GRID_CAP_SLACK)),
        )
        self.assertEqual(chrome_show.grid_cell_w(), expect)
        self.assertGreaterEqual(chrome_show.grid_cell_w(), chrome_show.GRID_CELL_MIN)
        # Dynamic: a longer caption widens every cell.
        grown = chrome_show.grid_cell_w(['Sel', 'VeryLongCaption'])
        self.assertGreater(grown, chrome_show.grid_cell_w(['Sel', 'Source']))
        here = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(here, 'chrome.py'), encoding='utf-8') as fh:
            chrome_txt = fh.read()
        metrics_fn = chrome_txt.split('def _grid_metrics', 1)[1].split(
            'def _grid_cell_props', 1,
        )[0]
        self.assertIn('grid_cell_w()', metrics_fn)
        bind_fn = chrome_txt.split('def _grid_bind_row', 1)[1].split(
            'def _apply_grid_label', 1,
        )[0]
        self.assertIn("'sp_r': 3", bind_fn)

    def test_grid_panel_min_w_formula_three_cells_plus_gutters(self):
        cell = chrome_show.grid_cell_w()
        cols = chrome_show.GRID_COLS
        gutters = (
            chrome_show.GRID_ROW_EDGE * 2
            + (cols - 1) * chrome_show.GRID_ROW_GUTTER * 2
            + chrome_show.GRID_SCROLL_PAD
        )
        expect = cols * cell + gutters
        self.assertEqual(chrome_show.grid_panel_min_w_formula(), expect)
        self.assertEqual(chrome_show.grid_panel_min_w_formula(cell), expect)
        # Default below mode @ 16px icons: longest cap "Inspect".
        self.assertEqual(expect, 174)
        # Live floor is owner lab minimum, not the formula.
        self.assertEqual(chrome_show.grid_panel_min_w(), 150)
        self.assertLess(chrome_show.grid_panel_min_w(), expect)
        here = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(here, 'chrome.py'), encoding='utf-8') as fh:
            chrome_txt = fh.read()
        self.assertIn('grid_panel_min_w', chrome_txt)
        self.assertIn('def _side_panel_min_w', chrome_txt)
        self.assertIn('def _apply_side_min_width', chrome_txt)
        size_fn = chrome_txt.split('def _size_side_grid', 1)[1].split(
            'def _fill_side_grid', 1,
        )[0]
        self.assertIn('_side_panel_min_w()', size_fn)
        self.assertIn("'w_min': min_w", size_fn)

    def test_grid_groups_partition_actions(self):
        flat = []
        for group in chrome_show.GRID_GROUPS:
            flat.extend(group)
        self.assertEqual(tuple(flat), chrome_show.ACTION_KEYS)
        self.assertEqual(len(flat), len(set(flat)))
        self.assertEqual(
            set(chrome_show.GRID_CAP),
            set(chrome_show.ACTION_KEYS),
        )

    def test_side_chrome_source_analytic_grid(self):
        here = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(here, 'chrome.py'), encoding='utf-8') as fh:
            text = fh.read()
        self.assertNotIn("'name': 'bar'", text)
        self.assertIn("'name': 'grid_scroll'", text)
        self.assertIn("DLG_CTL_ADD, 'scrollbox'", text)
        self.assertIn("'name': 'grid'", text)
        self.assertNotIn('chrome_show.side_plan', text)
        self.assertNotIn('bar_row_', text)
        self.assertNotIn('def _fill_side_row', text)
        self.assertNotIn('def _bar_add', text)
        self.assertNotIn('def _clear_side_bar', text)
        self.assertIn('IMAGELIST_CREATE', text)
        self.assertIn('_h_side_il', text)
        self.assertIn('_grid_bars', text)
        self.assertIn('ALIGN_NONE', text)
        self.assertIn('def _size_side_grid', text)
        self.assertIn('def _refresh_side_scroll', text)
        self.assertIn('_grid_content_h', text)
        self.assertIn("'name': 'status'", text)
        self.assertIn("'name': 'status_band'", text)
        self.assertIn("DLG_CTL_ADD, 'listbox'", text)
        self.assertNotIn("DLG_CTL_ADD, 'listbox_ex'", text)
        self.assertNotIn('LISTBOX_THEME', text)
        self.assertIn('def _set_status_band', text)
        self.assertIn("'icon': (26, 20)", text)
        self.assertIn("'below': (36, GRID_ICON_STRIP_H + GRID_CAP_H)", text)
        self.assertIn('GRID_CAP_H', text)
        self.assertIn('GRID_ICON_STRIP_H', text)
        self.assertIn('ALIGN_BOTTOM', text)
        self.assertIn('def _fill_side_grid', text)
        self.assertIn('chrome_show.grid_plan(prefs.get_chrome_show())', text)
        grid_fn = text.split('def _grid_add', 1)[1].split(
            'def _create_toolbar', 1,
        )[0]
        self.assertIn('BTN_SET_DATA1', grid_fn)
        self.assertNotIn("DLG_CTL_ADD, 'button_ex'", grid_fn)
        self.assertIn("cmd=' + method", grid_fn)
        self.assertIn('_grid_hdr', grid_fn)
        self.assertIn('_grid_bind_row', grid_fn)
        self.assertIn('grid_card_', grid_fn)
        self.assertIn('reversed(families)', grid_fn)
        self.assertIn('a_r', grid_fn)
        self.assertIn("startswith('gl_')", text)
        self.assertIn('def _sync_grid_caption', text)
        self.assertIn('BTNKIND_ICON_ONLY', grid_fn)
        self.assertIn('BTN_SET_BOLD', text)
        self.assertIn("'caption'", text)
        self.assertIn('get_grid_label', grid_fn)
        self.assertIn("mode == 'below'", grid_fn)
        self.assertIn('TOOLBAR_SET_VERTICAL', grid_fn)
        self.assertIn('def _apply_grid_label', text)
        self.assertIn('def _freeze_side', text)
        self.assertIn('DLG_LOCK', text)
        self.assertIn('DLG_UNLOCK', text)
        self.assertIn('BTN_SET_HINT', grid_fn)
        self.assertIn('TOOLBAR_THEME', grid_fn)
        self.assertIn('_theme_bar', grid_fn)
        self.assertIn('_apply_side_theme', text)
        self.assertIn('ButtonBgPassive', text)
        self.assertIn('TabBg', text)
        self.assertIn('theme_rgb', text)
        self.assertIn('self._apply_side_theme()', text)

    def test_menu_path_nests(self):
        self.assertEqual(chrome_show.menu_path('cfg'), 'Config')
        self.assertEqual(chrome_show.menu_path('send'), 'Send\\Send')
        self.assertEqual(chrome_show.menu_path('function'), 'Send\\Function')
        self.assertEqual(chrome_show.menu_path('source'), 'Source\\Source')
        self.assertEqual(chrome_show.menu_path('inspect'), 'Inspect\\Print')
        self.assertEqual(chrome_show.menu_path('ls'), 'Inspect\\ls()')
        self.assertEqual(chrome_show.menu_path('clear'), 'Clear\\Clear')
        self.assertEqual(chrome_show.menu_path('clear_all'), 'Clear\\Clear all')
        self.assertEqual(
            set(chrome_show.ACTION_METHODS),
            set(chrome_show.ACTION_KEYS),
        )

    def test_install_inf_menu_tree(self):
        here = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(here, 'install.inf'), encoding='utf-8') as fh:
            text = fh.read()
        by_method = {}
        for block in re.split(r'\n(?=\[item\d+\])', text):
            if 'section=commands' not in block:
                continue
            if re.search(r'(?m)^menu=0\s*$', block):
                continue
            cap_m = re.search(r'(?m)^caption=STATghost\\(.+)$', block)
            meth_m = re.search(r'(?m)^method=(\w+)\s*$', block)
            if not cap_m or not meth_m:
                continue
            by_method.setdefault(meth_m.group(1), []).append(cap_m.group(1))
        for key in chrome_show.ACTION_KEYS:
            method = chrome_show.ACTION_METHODS[key]
            expected = chrome_show.menu_path(key)
            self.assertIn(
                expected,
                by_method.get(method, []),
                '%s (%s) missing STATghost\\%s' % (key, method, expected),
            )

    def test_checklist_roundtrip(self):
        keys = ('cfg', 'send', 'clear')
        on = {'cfg': True, 'send': False, 'clear': True}
        raw = chrome_show.encode_checklist(on, keys)
        self.assertEqual(raw, '0;1,0,1')
        back = chrome_show.decode_checklist(raw, keys)
        self.assertEqual(back['cfg'], True)
        self.assertEqual(back['send'], False)
        self.assertEqual(back['clear'], True)
        short = chrome_show.decode_checklist('0;1', keys, fallback=on)
        self.assertEqual(short, on)

    def test_config_source_is_dlg_proc_pages(self):
        here = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(here, 'config.py'), encoding='utf-8') as fh:
            text = fh.read()
        self.assertIn("PAGES = ('Send', 'Chrome', 'Host')", text)
        self.assertIn('dlg_proc', text)
        self.assertNotIn('from cudatext import dlg_custom', text)
        self.assertIn('cmd=config_dlg', text)
        self.assertIn('Keep editor focused after Send', text)
        self.assertIn('keep_focus', text)
        self.assertIn('ALIGN_CLIENT', text)
        self.assertIn('a_r', text)
        self.assertIn("'name': 'keep_hint'", text)
        self.assertIn("'name': 'host_exe'", text)
        self.assertIn("'name': 'host_det'", text)
        self.assertIn("'name': 'grid_label'", text)
        self.assertIn("'name': 'chrome_grid'", text)
        self.assertIn("'cap': 'Apply'", text)
        self.assertIn("'name': 'btn_apply'", text)
        self.assertIn("kind == 'apply'", text)
        self.assertIn("_CB % 'apply'", text)
        self.assertIn('ALIGN_BOTTOM', text)
        self.assertIn("a_r': ('btn_ok', '[')", text)
        self.assertIn('def _snapshot_prefs', text)
        self.assertIn('def _restore_prefs', text)
        self.assertIn('rebuild_chrome', text)
        chrome = text.split('def _fill_chrome', 1)[1].split('def _fill_host', 1)[0]
        self.assertIn('ALIGN_TOP', chrome)
        self.assertIn('a_r', chrome)
        self.assertIn('_GRID_LABEL_ITEMS', chrome)
        self.assertIn('below  (caption under icon)', text)
        self.assertNotIn('dlg_custom', chrome)
        send = text.split('def _fill_send', 1)[1].split('def _fill_chrome', 1)[0]
        self.assertIn("'ex3': True", send)
        host_fn = text.split('def _fill_host', 1)[1].split('def show_config', 1)[0]
        self.assertNotIn('ALIGN_CLIENT', host_fn)
        self.assertIn("'ex3': True", host_fn)

    def test_config_nav_width_is_longest_plus_20pct(self):
        here = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(here, 'config.py')
        with open(path, encoding='utf-8') as fh:
            lines = fh.readlines()
        text = ''.join(lines).replace('\r\n', '\n')
        self.assertIn('_TREE_SLACK = 1.20', text)
        self.assertIn('def _apply_nav_width(', text)
        start = next(
            i for i, line in enumerate(lines) if line.startswith('_TREE_SLACK')
        )
        consts_end = next(
            i for i, line in enumerate(lines) if line.startswith('_EMU_CHAR')
        )
        fn_start = next(
            i for i, line in enumerate(lines) if line.startswith('def nav_width')
        )
        fn_end = next(
            i for i, line in enumerate(lines[fn_start + 1 :], fn_start + 1)
            if line.startswith('def ')
        )
        ns = {}
        exec(
            ''.join(lines[start:consts_end + 1] + ['\n'] + lines[fn_start:fn_end]),
            ns,
        )
        nav_width = ns['nav_width']
        # 100 * 1.20 + 24 gutter
        self.assertEqual(nav_width(100), 144)
        self.assertEqual(nav_width(0), ns['_TREE_MIN'])
        self.assertEqual(nav_width(9999), ns['_TREE_MAX'])
        self.assertLess(nav_width(48), 150)

    def test_cli_cycle_subset(self):
        self.assertTrue(chrome_show.CYCLE_METHODS <= chrome_show.CLI_METHODS)
        self.assertIn('inspect_ls', chrome_show.CLI_METHODS)
        self.assertNotIn('config', chrome_show.CLI_METHODS)
        self.assertNotIn('toggle_host', chrome_show.CLI_METHODS)


class TestRWord(unittest.TestCase):
    def test_identifier_plain_and_pkg(self):
        line = '  iris <- stats::sd(x)'
        self.assertEqual(rword.identifier_at(line, 4), 'iris')
        self.assertEqual(rword.identifier_at(line, 14), 'stats::sd')
        self.assertTrue(rword.is_ref('iris$Sepal.Length'))
        self.assertEqual(
            rword.identifier_at('plot(iris$Sepal.Length)', 10),
            'iris$Sepal.Length',
        )

    def test_print_vs_wrap(self):
        self.assertEqual(rword.print_target('  iris  ', '', 0), 'iris')
        self.assertEqual(rword.print_target('1 + 1', 'iris', 0), '1 + 1')
        self.assertEqual(rword.wrap_target('1 + 1', 'iris', 2), '')
        self.assertEqual(rword.wrap_target('', '  iris <- 1', 4), 'iris')
        self.assertEqual(rword.wrap_code('str', 'iris'), 'str(iris)')
        self.assertEqual(rword.help_code('stats::sd'), "help(sd, package='stats')")
        self.assertEqual(rword.help_code('mean'), 'help(mean)')
        self.assertEqual(rword.help_code('iris$x'), '')

    def test_empty_caret(self):
        self.assertEqual(rword.identifier_at('# comment', 0), '')
        self.assertEqual(rword.identifier_at('1 + 2', 2), '')
        self.assertEqual(rword.print_target('', '', 0), '')


class TestIconFg(unittest.TestCase):
    def test_force_modes(self):
        bg = (0x1C, 0x1C, 0x1C)
        font = (0x44, 0x44, 0x44)
        self.assertEqual(icons_fg.pick_fg_rgb('light', font, bg), (0xC4, 0xC4, 0xC4))
        self.assertEqual(icons_fg.pick_fg_rgb('dark', font, bg), (0x3A, 0x3A, 0x3A))
        self.assertEqual(icons_fg.pick_fg_rgb('gray', font, bg), (0x8A, 0x8A, 0x8A))
        self.assertEqual(icons_fg.pick_fg_rgb('theme', font, bg), font)

    def test_auto_rejects_dark_on_dark(self):
        bg = (0x1C, 0x1C, 0x1C)
        font = (0x44, 0x44, 0x44)
        fg = icons_fg.pick_fg_rgb('auto', font, bg)
        self.assertEqual(fg, icons_fg.FG_WHITE)
        self.assertGreaterEqual(icons_fg.contrast_ratio(fg, bg), 3.0)

    def test_auto_keeps_good_buttonfont(self):
        bg = (0x1C, 0x1C, 0x1C)
        font = (0xE0, 0xE0, 0xE0)
        fg = icons_fg.pick_fg_rgb('auto', font, bg)
        self.assertGreaterEqual(icons_fg.contrast_ratio(fg, bg), 3.0)
        self.assertGreater(icons_fg.rel_luma(fg), 0.5)


class TestOutline(unittest.TestCase):
    def test_sections_and_functions(self):
        src = '''\
# ---- Setup ----
x <- 1

## Model
fit <- function(y) {
  y
}
'''
        rows = _lines(src)
        items = outline.collect_outline(_get(rows), len(rows))
        kinds = [it['kind'] for it in items]
        self.assertIn('section', kinds)
        self.assertIn('function', kinds)
        titles = [it['title'] for it in items]
        self.assertTrue(any('Setup' in t or t == 'Setup' for t in titles))
        self.assertIn('fit', titles)


class TestRanges(unittest.TestCase):
    def test_above_below(self):
        rows = _lines('a\nb\nc\n')
        self.assertEqual(ranges.lines_from_start(_get(rows), 1, len(rows)), 'a\nb')
        self.assertEqual(ranges.lines_to_end(_get(rows), 1, len(rows)), 'b\nc\n')

    def test_sniper_chunk(self):
        rows = _lines('a <- 1\nb <- 2\n\nc <- 3\n')

        def is_cut(line):
            s = (line or '').strip()
            return s == '' or s.startswith('#')

        s, e = ranges.sniper_chunk_bounds(0, _get(rows), len(rows), is_cut)
        self.assertEqual((s, e), (0, 1))
        s2, e2 = ranges.sniper_chunk_bounds(3, _get(rows), len(rows), is_cut)
        self.assertEqual((s2, e2), (3, 3))


def _span(src, y):
    rows = _lines(src)
    s, e = statement.extend_statement(y, _get(rows), len(rows))
    return s, e, statement.dedent_block(statement.join_lines(_get(rows), s, e))


def _send_at(src, y):
    rows = _lines(src)
    n = len(rows)
    get = _get(rows)
    fs, fe = statement.enclosing_function(y, get, n)
    if fs is not None and fe is not None:
        text = statement.join_lines(get, fs, fe)
        return fs, fe, statement.dedent_block(text), 'function'
    s, e = statement.extend_statement(y, get, n)
    text = statement.join_lines(get, s, e)
    return s, e, statement.dedent_block(text), 'statement'


class TestExtendStatement(unittest.TestCase):
    def test_r_wrapped_call(self):
        src = 'rnorm(n = 1e2,\n      mean = 10,\n      sd = 2)\n'
        s, e, text = _span(src, 0)
        self.assertEqual((s, e), (0, 2))
        self.assertIn('sd = 2)', text)

    def test_r_unbraced_if(self):
        src = (
            'if (!requireNamespace("magrittr", quietly = TRUE))\n'
            '  install.packages("magrittr")\n'
            'library(magrittr)\n'
        )
        s, e, text = _span(src, 0)
        self.assertEqual(s, 0)
        self.assertEqual(e, 1)
        self.assertIn('install.packages', text)
        self.assertNotIn('library', text)

    def test_r_if_else(self):
        src = 'if (x > 0)\n  1\nelse\n  2\nnext <- 3\n'
        s, e, _text = _span(src, 0)
        self.assertEqual((s, e), (0, 3))

    def test_triple_quoted_string(self):
        src = 'text = """\nhello\n"""\npat = 1\n'
        s, e, text = _span(src, 0)
        self.assertEqual((s, e), (0, 2))
        self.assertIn('hello', text)
        self.assertTrue(text.rstrip().endswith('"""'))

    def test_caret_inside_triple_quoted_string(self):
        src = 'text = """\nhello\n"""\npat = 1\n'
        s, e, text = _span(src, 1)
        self.assertEqual((s, e), (0, 2))
        ast.parse(text)
        s2, e2, text2 = _span(src, 2)
        self.assertEqual((s2, e2), (0, 2))
        ast.parse(text2)


class TestDedent(unittest.TestCase):
    def test_method_becomes_module_def(self):
        src = '    def dist2(self):\n        return self.x\n'
        out = statement.dedent_block(src)
        ast.parse(out)
        self.assertTrue(out.startswith('def dist2'))


class TestPythonCompound(unittest.TestCase):
    def test_try_except_else_from_header(self):
        src = (
            'try:\n'
            '    import numpy as np\n'
            'except ImportError:\n'
            '    print("SKIP")\n'
            'else:\n'
            '    np.random.seed(17)\n'
            'done = 1\n'
        )
        s, e, text = _span(src, 0)
        self.assertEqual((s, e), (0, 5))
        ast.parse(text)
        self.assertNotIn('done', text)

    def test_except_walks_back_to_try(self):
        src = (
            'try:\n'
            '    import numpy as np\n'
            'except ImportError:\n'
            '    print("SKIP")\n'
        )
        s, e, text = _span(src, 2)
        self.assertEqual(s, 0)
        ast.parse(text)

    def test_inner_line_stays_one_statement(self):
        src = (
            'try:\n'
            '    import numpy as np\n'
            'except ImportError:\n'
            '    print("SKIP")\n'
        )
        _s, _e, text, mode = _send_at(src, 1)
        self.assertEqual(mode, 'statement')
        self.assertEqual(text.strip(), 'import numpy as np')
        ast.parse(text)

    def test_inner_print_does_not_steal_else(self):
        src = (
            'if cond:\n'
            '    print("SKIP")\n'
            'else:\n'
            '    x = 1\n'
        )
        _s, _e, text, mode = _send_at(src, 1)
        self.assertEqual(mode, 'statement')
        self.assertEqual(text.strip(), 'print("SKIP")')
        ast.parse(text)

    def test_decorator_plus_class(self):
        src = (
            '@dataclass\n'
            'class RunningMean:\n'
            '    n: int = 0\n'
            '    def update(self, x):\n'
            '        return x\n'
            'rm = RunningMean()\n'
        )
        s, e, text, mode = _send_at(src, 0)
        self.assertEqual(mode, 'function')
        self.assertEqual(s, 0)
        self.assertIn('@dataclass', text)
        self.assertIn('class RunningMean', text)
        self.assertNotIn('rm =', text)
        ast.parse(text)

    def test_for_try_from_for_header(self):
        src = (
            'total = 0\n'
            'for i in range(5):\n'
            '    try:\n'
            '        if i == 3:\n'
            '            raise ValueError("boom")\n'
            '        total += i\n'
            '    except ValueError as e:\n'
            '        print(e)\n'
            'print(total)\n'
        )
        s, e, text = _span(src, 1)
        self.assertEqual(s, 1)
        self.assertIn('except ValueError', text)
        ast.parse(text)


def _sample_root():
    env = os.environ.get('STATGHOST_SAMPLE')
    if env and os.path.isdir(env):
        return env
    root = host.sibling_dir('statghost')
    if root:
        cand = os.path.join(root, 'sample')
        if os.path.isdir(os.path.join(cand, 'R')):
            return cand
    return None


def _is_cut(line):
    s = (line or '').strip()
    return s == '' or s.startswith('#')


def _collect_extracts(path):
    with open(path, encoding='utf-8') as f:
        rows = _lines(f.read())
    out = []
    seen = set()
    for y, line in enumerate(rows):
        if _is_cut(line):
            continue
        s, e, text, mode = _send_at('\n'.join(rows), y)
        key = (s, e, mode)
        if key in seen:
            continue
        seen.add(key)
        out.append((os.path.basename(path), y + 1, mode, text))
    return out


def _r_parse_batch(items):
    if not items:
        return []
    tmp = tempfile.mkdtemp(prefix='sgtf_')
    files = []
    for i, (_n, _y, _m, text) in enumerate(items):
        p = os.path.join(tmp, '%04d.R' % i)
        with open(p, 'w', encoding='utf-8') as f:
            f.write(text or '')
        files.append(p)
    checker = os.path.join(tmp, 'check.R')
    with open(checker, 'w', encoding='utf-8') as f:
        f.write(
            'files <- commandArgs(TRUE)\n'
            'for (i in seq_along(files)) {\n'
            '  e <- tryCatch(parse(file = files[[i]], keep.source = TRUE),\n'
            '                error = function(err) err)\n'
            '  if (inherits(e, "error"))\n'
            '    cat(sprintf("FAIL\\t%d\\t%s\\n", i - 1L, conditionMessage(e)))\n'
            '}\n'
        )
    p = subprocess.run(
        ['Rscript', '--vanilla', checker] + files,
        capture_output=True, text=True, timeout=60,
    )
    fails = []
    for line in (p.stdout or '').splitlines():
        if not line.startswith('FAIL\t'):
            continue
        parts = line.split('\t', 2)
        if len(parts) >= 3:
            fails.append((items[int(parts[1])], parts[2]))
    return fails


class TestSampleExtracts(unittest.TestCase):
    """Automatic classroom gate: every unique Send extract must parse."""

    @classmethod
    def setUpClass(cls):
        cls.root = _sample_root()

    def test_r_samples_parse(self):
        if not self.root:
            self.skipTest('STATghost sample/ not found')
        items = []
        rdir = os.path.join(self.root, 'R')
        for name in sorted(os.listdir(rdir)):
            if name.endswith('.R'):
                items.extend(_collect_extracts(os.path.join(rdir, name)))
        self.assertGreater(len(items), 50)
        fails = _r_parse_batch(items)
        self.assertEqual(
            fails, [],
            '\n'.join(
                '%s L%s %s: %s' % (n, y, m, err)
                for (n, y, m, _t), err in fails
            ),
        )

    def test_python_samples_parse(self):
        if not self.root:
            self.skipTest('STATghost sample/ not found')
        fails = []
        pdir = os.path.join(self.root, 'Python')
        n = 0
        for name in sorted(os.listdir(pdir)):
            if not name.endswith('.py') or name == 'run_tests.py':
                continue
            for fname, y, mode, text in _collect_extracts(os.path.join(pdir, name)):
                n += 1
                try:
                    ast.parse(text or '')
                except SyntaxError as e:
                    fails.append('%s L%s %s: %s' % (fname, y, mode, e.msg))
        self.assertGreater(n, 50)
        self.assertEqual(fails, [], '\n'.join(fails))


class TestSiblingDir(unittest.TestCase):
    def test_finds_statghost_sample(self):
        root = host.sibling_dir('statghost')
        self.assertTrue(root)
        self.assertTrue(os.path.isdir(os.path.join(root, 'sample', 'R')))
        here = os.path.dirname(os.path.realpath(host.__file__))
        self.assertFalse(host._is_under(here, root))

    def test_sibling_exe_under_statghost(self):
        root = host.sibling_dir('statghost')
        exe = host._sibling_exe()
        self.assertTrue(os.path.normcase(exe).startswith(os.path.normcase(root)))

    def test_cudatext_is_not_host_folder(self):
        """Windows: plugins/cudatext must not satisfy sibling_dir('CudaText')."""
        here = os.path.dirname(os.path.realpath(host.__file__))
        host_folder = os.path.abspath(os.path.dirname(here))
        root = host.sibling_dir('CudaText')
        if root:
            self.assertNotEqual(
                os.path.normcase(host_folder),
                os.path.normcase(os.path.abspath(root)),
            )
            self.assertFalse(host._is_under(here, root))
            self.assertTrue(
                os.path.isdir(os.path.join(root, 'app', 'py'))
                or os.path.isfile(os.path.join(root, 'app', 'cudatext.exe'))
                or os.path.isfile(os.path.join(root, 'app', 'cudatext')),
            )


if __name__ == '__main__':
    unittest.main(verbosity=2)
