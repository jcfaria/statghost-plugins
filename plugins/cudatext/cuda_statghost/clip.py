# Fan-out clipboard so STATghost sees ARM/EVAL from any host widgetset.
# CudaText gtk2 → X11. CudaText Qt6 on Plasma → Wayland. STATghost may be
# either. Write native + X11 + Wayland; each hop is best-effort.
# Never capture xclip stdout (it stays clipboard owner and deadlocks).

from __future__ import annotations

import shutil
import subprocess
import sys


def push(text, native=None):
    data = text if isinstance(text, str) else ''
    if native is not None:
        try:
            native(data)
        except Exception:
            pass
    if sys.platform.startswith('win'):
        return True
    _try_x11(data)
    _try_wayland(data)
    return True


def _popen_in(args, raw):
    p = subprocess.Popen(
        args,
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        p.communicate(input=raw, timeout=1)
    except subprocess.TimeoutExpired:
        return True
    return p.returncode in (0, None)


def _try_x11(data):
    raw = data.encode('utf-8')
    if shutil.which('xclip'):
        try:
            return _popen_in(['xclip', '-selection', 'clipboard', '-in'], raw)
        except OSError:
            pass
    if shutil.which('xsel'):
        try:
            subprocess.run(
                ['xsel', '--clipboard', '--input'],
                input=raw,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=2,
            )
            return True
        except (OSError, subprocess.TimeoutExpired):
            return False
    return False


def _try_wayland(data):
    if not shutil.which('wl-copy'):
        return False
    try:
        subprocess.run(
            ['wl-copy', '--type', 'text/plain'],
            input=data.encode('utf-8'),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=2,
        )
        return True
    except (OSError, subprocess.TimeoutExpired):
        return False
