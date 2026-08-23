#!/usr/bin/env python3
# Functional validation of cuda_statghost against a *running* STATghost.
# Uses the same clipboard contract as the plugin (protocol.py). No GUI clicks.
# Does not Quit / Idle the interactive instance.
#
#   python3 test_functional.py
#
# Requires: STATghost running + Armed-capable session, DISPLAY, xclip|wl-copy.

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import host  # noqa: E402
import paths  # noqa: E402
import protocol  # noqa: E402
import statement  # noqa: E402

MARKER_DIR = os.path.join(paths.temp_root(), 'STATghost')
POLL_S = 0.15
ARM_WAIT_S = 8.0
EVAL_WAIT_S = 20.0


def _clip_tool():
    if sys.platform.startswith('win'):
        return 'win32'
    if shutil.which('xclip'):
        return 'xclip'
    if shutil.which('wl-copy'):
        return 'wl-copy'
    if shutil.which('xsel'):
        return 'xsel'
    return None


def set_clip(text):
    if sys.platform.startswith('win'):
        import test_workbar as wb
        return wb._set_clip(text)
    """Put UTF-8 on the X/Wayland clipboard. Never capture xclip pipes
    (it stays as clipboard owner and capture_output deadlocks)."""
    data = text if isinstance(text, str) else ''
    tool = _clip_tool()
    if tool == 'xclip':
        p = subprocess.Popen(
            ['xclip', '-selection', 'clipboard', '-in'],
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        try:
            p.communicate(input=data.encode('utf-8'), timeout=1)
        except subprocess.TimeoutExpired:
            return True
        return p.returncode in (0, None)
    if tool == 'wl-copy':
        p = subprocess.run(
            ['wl-copy'], input=data, text=True,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            timeout=3,
        )
        return p.returncode == 0
    if tool == 'xsel':
        p = subprocess.run(
            ['xsel', '--clipboard', '--input'],
            input=data, text=True,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            timeout=3,
        )
        return p.returncode == 0
    return False


def wait_file(path, timeout, expect=''):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if os.path.isfile(path):
            try:
                with open(path, encoding='utf-8') as fh:
                    raw = fh.read()
            except OSError:
                raw = ''
            if expect == '' or expect in raw:
                return True, raw
        time.sleep(POLL_S)
    return False, ''


def marker_path(tag):
    os.makedirs(MARKER_DIR, exist_ok=True)
    return os.path.join(MARKER_DIR, 'cuda_plugin_tf_%s.txt' % tag)


def r_write(path, token):
    q = path.replace('\\', '/')
    return (
        'dir.create(%s, showWarnings = FALSE, recursive = TRUE)\n'
        'writeLines(%s, %s)\n'
        % (
            repr(os.path.dirname(q)),
            repr(token),
            repr(q),
        )
    )


def send_eval(code):
    msg = protocol.make_eval(code)
    cmd, body = protocol.parse_message(msg)
    if cmd != protocol.CMD_EVAL or body != code:
        return False, 'protocol roundtrip failed'
    if sys.platform.startswith('win'):
        import test_workbar as wb
        wb._nudge_sg()
        time.sleep(0.25)
    if not set_clip(msg):
        return False, 'clipboard set failed'
    return True, msg


class TestFunctionalLive(unittest.TestCase):
    """Live clipboard → STATghost. Leaves the interactive instance up."""

    @classmethod
    def setUpClass(cls):
        cls.tool = _clip_tool()
        cls.running = host.is_running()
        if not cls.tool:
            raise unittest.SkipTest('no xclip/wl-copy/xsel on PATH')
        if (
            cls.tool not in ('win32', 'wl-copy')
            and not os.environ.get('DISPLAY')
        ):
            raise unittest.SkipTest('DISPLAY unset (clipboard needs an X session)')
        if not cls.running:
            raise unittest.SkipTest(
                'STATghost is not running — start it, Arm R, re-run'
            )
        if sys.platform.startswith('win'):
            import test_workbar as wb
            wb._nudge_sg()
        if not set_clip(protocol.make_command(protocol.CMD_ARM)):
            raise unittest.SkipTest('could not put ARM on the clipboard')
        time.sleep(ARM_WAIT_S)

    def test_01_host_up(self):
        self.assertTrue(host.is_running())
        self.assertTrue(host.has_app_window() or host.is_running())

    def test_02_eval_write_marker(self):
        tag = 'eval_%s' % protocol._nonce()
        path = marker_path(tag)
        if os.path.isfile(path):
            os.remove(path)
        ok, err = send_eval(r_write(path, tag))
        self.assertTrue(ok, err)
        found, raw = wait_file(path, EVAL_WAIT_S, tag)
        self.assertTrue(
            found,
            'STATghost did not write marker %s — is R Armed?' % path,
        )
        self.assertIn(tag, raw)

    def test_03_nonce_rerun_same_code(self):
        """Same student chunk twice must both fire (nonce)."""
        tag_a = 'rerun_a_%s' % protocol._nonce()
        tag_b = 'rerun_b_%s' % protocol._nonce()
        path = marker_path('rerun')
        if os.path.isfile(path):
            os.remove(path)
        ok, err = send_eval(r_write(path, tag_a))
        self.assertTrue(ok, err)
        found, _ = wait_file(path, EVAL_WAIT_S, tag_a)
        self.assertTrue(found, 'first rerun send did not land')
        time.sleep(0.4)
        ok, err = send_eval(r_write(path, tag_b))
        self.assertTrue(ok, err)
        found, raw = wait_file(path, EVAL_WAIT_S, tag_b)
        self.assertTrue(found, 'second identical-shape send was skipped')
        self.assertIn(tag_b, raw)

    def test_04_collapse_then_eval(self):
        tag = 'collapse_%s' % protocol._nonce()
        path = marker_path(tag)
        if os.path.isfile(path):
            os.remove(path)
        wrapped = (
            'writeLines(\n'
            '  %s,\n'
            '  %s)\n'
            % (repr(tag), repr(path.replace('\\', '/')))
        )
        collapsed = statement.collapse_wraps(wrapped).strip()
        self.assertEqual(collapsed.count('\n'), 0, collapsed)
        ok, err = send_eval(collapsed)
        self.assertTrue(ok, err)
        found, raw = wait_file(path, EVAL_WAIT_S, tag)
        self.assertTrue(found, 'collapsed wrap did not eval')
        self.assertIn(tag, raw)

    def test_05_source_slot4(self):
        """Plugin Source-file path: write .paths[4], eval source(.paths[n])."""
        tag = 'slot4_%s' % protocol._nonce()
        path = marker_path(tag)
        if os.path.isfile(path):
            os.remove(path)
        body = r_write(path, tag)
        slot = paths.write_slot(paths.IDX_FILE, body)
        self.assertTrue(os.path.isfile(slot))
        code = (
            'source(.paths[%d], echo = FALSE, spaced = FALSE, encoding = "UTF-8")'
            % paths.IDX_FILE
        )
        ok, err = send_eval(code)
        self.assertTrue(ok, err)
        found, raw = wait_file(path, EVAL_WAIT_S, tag)
        self.assertTrue(
            found,
            'source(.paths[4]) did not run — companion loaded? R Armed?',
        )
        self.assertIn(tag, raw)

    def test_06_extract_sample_statement_then_eval(self):
        """Caret-style extract from sample 01, then a safe live eval of 1+1."""
        root = host.sibling_dir('statghost')
        sample = os.path.join(root, 'sample', 'R', '01_hello.R') if root else ''
        if not os.path.isfile(sample):
            self.skipTest('sample 01_hello.R not found')
        with open(sample, encoding='utf-8') as fh:
            rows = fh.read().replace('\r\n', '\n').split('\n')

        def get(i):
            return rows[i] if 0 <= i < len(rows) else ''

        # Line `1 + 1` in the sample
        y = next(i for i, ln in enumerate(rows) if ln.strip() == '1 + 1')
        s, e = statement.extend_statement(y, get, len(rows))
        text = statement.dedent_block(statement.join_lines(get, s, e))
        self.assertEqual(text.strip(), '1 + 1')
        tag = 'hello_%s' % protocol._nonce()
        path = marker_path(tag)
        if os.path.isfile(path):
            os.remove(path)
        # Bind the extracted expression into the marker write.
        code = 'invisible(%s)\n%s' % (text.strip(), r_write(path, tag))
        ok, err = send_eval(code)
        self.assertTrue(ok, err)
        found, raw = wait_file(path, EVAL_WAIT_S, tag)
        self.assertTrue(found, 'extracted 1+1 pipeline did not eval')
        self.assertIn(tag, raw)

    def test_07_clear_does_not_eval(self):
        """CLEAR is a control token — must not be eval'd as R."""
        tag = 'clear_%s' % protocol._nonce()
        path = marker_path(tag)
        if os.path.isfile(path):
            os.remove(path)
        if sys.platform.startswith('win'):
            import test_workbar as wb
            wb._nudge_sg()
            time.sleep(0.25)
        self.assertTrue(set_clip(protocol.make_command(protocol.CMD_CLEAR)))
        time.sleep(0.8)
        self.assertFalse(
            os.path.isfile(path),
            'CLEAR must not create an eval marker',
        )
        ok, err = send_eval(r_write(path, tag))
        self.assertTrue(ok, err)
        found, _ = wait_file(path, EVAL_WAIT_S, tag)
        self.assertTrue(found, 'eval after CLEAR did not land')


if __name__ == '__main__':
    print(
        'functional: sg_running=%s clip=%s display=%s'
        % (host.is_running(), _clip_tool(), os.environ.get('DISPLAY', '')),
        flush=True,
    )
    unittest.main(verbosity=2)
