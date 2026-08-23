#!/usr/bin/env python3
# Automatic production TF: running CudaText plugin → running STATghost.
# No human hands. Opens sample tabs, fires the *configured* Send hotkey,
# asserts STATghost clip.R got the statement.
#
# Live EVAL must be valid for the *armed* engine (this lab: R). Python
# extract stays in test_unit.py — sending def/for into R paints Error:
# on the Console. Chunks that need session objects (predict(m_1)) are
# sent only after the assignment that creates them.
#
#   /tmp/sg_prod_venv/bin/python test_production.py
#   python3 test_production.py          # needs python-xlib + wmctrl + xclip

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import host  # noqa: E402
import protocol  # noqa: E402

_SG = host.sibling_dir('statghost') or ''
SAMPLE = os.path.join(_SG, 'sample') if _SG else ''
SAMPLE_R = os.path.join(SAMPLE, 'R')
SAMPLE_PY = os.path.join(SAMPLE, 'Python')
KEYS_JSON = os.path.expanduser('~/.config/cudatext/settings/keys.json')
_KEYSYM = {
    'ctrl': 'Control_L',
    'control': 'Control_L',
    'shift': 'Shift_L',
    'alt': 'Alt_L',
    'enter': 'Return',
    'return': 'Return',
    'space': 'space',
    'escape': 'Escape',
    'esc': 'Escape',
}


def _cuda_exe():
    if sys.platform.startswith('win'):
        try:
            import test_workbar as wb
            return wb.CUDA_EXE or None
        except Exception:
            return None
    try:
        out = subprocess.check_output(['pgrep', '-ax', 'cudatext'], text=True)
    except (OSError, subprocess.CalledProcessError):
        out = ''
    for line in out.splitlines():
        parts = line.split(None, 1)
        if len(parts) == 2 and os.path.isfile(parts[1].split()[0]):
            return parts[1].split()[0]
    for p in (
        '/home/jcfaria/Documentos/Github/CudaText/app/bin/linux-amd64-gtk2/cudatext',
        '/home/jcfaria/Documentos/Github/CudaText/app/cudatext',
    ):
        if os.path.isfile(p):
            return p
    return None


def _sg_pid():
    pids = host.list_pids()
    return pids[0] if pids else None


def _clip_path(pid):
    return '/tmp/statghost_%s/clip.R' % pid


def _hotkey(method, default):
    try:
        with open(KEYS_JSON, encoding='utf-8') as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        data = {}
    row = data.get('cuda_statghost,' + method) or {}
    chords = row.get('s1') or []
    if chords:
        return chords[0]
    return default


def _chord_to_keysyms(chord):
    out = []
    for part in (chord or '').split('+'):
        p = part.strip()
        if not p:
            continue
        key = _KEYSYM.get(p.lower(), p if len(p) > 1 else p.lower())
        out.append(key)
    return out


def _set_clip(text):
    p = subprocess.Popen(
        ['xclip', '-selection', 'clipboard', '-in'],
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        p.communicate(input=text.encode('utf-8'), timeout=1)
    except subprocess.TimeoutExpired:
        pass


def _cuda_row():
    try:
        out = subprocess.check_output(['wmctrl', '-lx'], text=True)
    except (OSError, subprocess.CalledProcessError):
        return None
    for line in out.splitlines():
        if 'cudatext.Cudatext' in line or 'CudaText' in line:
            return line
    return None


def _cuda_wid():
    row = _cuda_row()
    if not row:
        return None
    return int(row.split()[0], 16)


def _cuda_title():
    row = _cuda_row()
    if not row:
        return ''
    parts = row.split(None, 4)
    return parts[4] if len(parts) > 4 else ''


def _focus(wid):
    from Xlib import X, display
    subprocess.run(
        ['wmctrl', '-i', '-a', hex(wid)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    d = display.Display()
    try:
        d.create_resource_object('window', wid).set_input_focus(
            X.RevertToParent, X.CurrentTime,
        )
        d.sync()
    except Exception:
        pass
    time.sleep(0.25)


def _send_chord(chord):
    from Xlib import X, XK, display
    from Xlib.ext import xtest
    names = _chord_to_keysyms(chord)
    d = display.Display()
    codes = []
    for name in names:
        ks = XK.string_to_keysym(name)
        kc = d.keysym_to_keycode(ks) if ks else 0
        if not kc:
            raise RuntimeError('no keycode for %s (chord %s)' % (name, chord))
        codes.append(kc)
    for kc in codes:
        xtest.fake_input(d, X.KeyPress, kc)
    d.sync()
    time.sleep(0.05)
    for kc in reversed(codes):
        xtest.fake_input(d, X.KeyRelease, kc)
    d.sync()


def _read(path):
    try:
        with open(path, encoding='utf-8') as fh:
            return fh.read()
    except OSError:
        return ''


class TestProductionCudaToSG(unittest.TestCase):
    """Hands-off: CudaText tab + plugin hotkey → STATghost clip.R."""

    @classmethod
    def setUpClass(cls):
        cls.exe = _cuda_exe()
        cls.sg = _sg_pid()
        cls.wid = _cuda_wid()
        cls.clip = _clip_path(cls.sg) if cls.sg else ''
        cls.send = _hotkey('send_selection', 'Ctrl+Enter')
        if not cls.exe or not os.path.isfile(cls.exe):
            raise unittest.SkipTest('CudaText is not running')
        if not cls.sg:
            raise unittest.SkipTest('STATghost is not running')
        if not cls.wid:
            raise unittest.SkipTest('CudaText window not found (wmctrl)')
        if not os.path.isdir(SAMPLE_R) or not os.path.isdir(SAMPLE_PY):
            raise unittest.SkipTest('statghost/sample not found')
        try:
            from Xlib.ext import xtest  # noqa: F401
        except ImportError:
            raise unittest.SkipTest('python-xlib missing (use /tmp/sg_prod_venv)')
        _set_clip(protocol.make_command(protocol.CMD_ARM))
        time.sleep(0.5)
        print(
            'production: cuda=%s sg=%s send=%s' % (cls.exe, cls.sg, cls.send),
            flush=True,
        )

    def _open(self, rel, line_1based):
        path = os.path.join(SAMPLE, rel)
        self.assertTrue(os.path.isfile(path), path)
        want = os.path.basename(path)
        subprocess.Popen(
            [self.exe, '%s@%d' % (path, line_1based)],
            start_new_session=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        deadline = time.time() + 10.0
        title = ''
        while time.time() < deadline:
            title = _cuda_title()
            if want in title:
                _focus(self.wid)
                time.sleep(0.35)
                return
            time.sleep(0.15)
        self.fail('CudaText did not show %s (title=%r)' % (want, title))

    def _send_and_wait(self, needle, timeout=10.0):
        last = ''
        for attempt in range(3):
            _set_clip(protocol.make_command(protocol.CMD_ARM))
            time.sleep(0.2)
            _focus(self.wid)
            _send_chord('Escape')
            time.sleep(0.08)
            _send_chord(self.send)
            deadline = time.time() + timeout
            while time.time() < deadline:
                last = _read(self.clip)
                if needle in last:
                    return last
                time.sleep(0.12)
        self.fail(
            'plugin Send (%s) did not put %r into %s\n--- title ---\n%s\n'
            '--- clip.R ---\n%s'
            % (self.send, needle, self.clip, _cuda_title(), last[:400])
        )

    def test_01_hello_one_plus_one(self):
        self._open('R/01_hello.R', 7)
        text = self._send_and_wait('1 + 1')
        self.assertIn('1 + 1', text)

    def test_02_hello_rnorm_wrap(self):
        self._open('R/01_hello.R', 9)
        text = self._send_and_wait('rnorm')
        self.assertIn('rnorm', text)
        self.assertIn('sd = 2', text)

    def test_03_sample12_bod(self):
        self._open('R/12_rl_linear_vs_nlinear.R', 36)
        text = self._send_and_wait('BOD')
        self.assertTrue(
            'BOD' in text.splitlines()[0] or text.strip() == 'BOD'
            or 'str(BOD)' in text or 'BOD' in text,
        )

    def test_04_sample12_nls_then_with(self):
        self._open('R/12_rl_linear_vs_nlinear.R', 37)
        text = self._send_and_wait('nls(demand')
        self.assertIn('data = BOD', text)
        self._open('R/12_rl_linear_vs_nlinear.R', 87)
        text = self._send_and_wait('with(BOD')
        self.assertIn('plot(demand ~ Time', text)
        self.assertIn('predict(m_1)', text)
        self.assertIn('})', text)


if __name__ == '__main__':
    unittest.main(verbosity=2)
