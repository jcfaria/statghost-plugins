# Locate / start the STATghost process. Quit is a clipboard command (protocol).
# Search order: plugin INI (Config UI) → STATGHOST_EXE → sibling clone → PATH.
# realpath() is required: CudaText lab installs the plugin as a symlink, and
# abspath(__file__) then walks into CudaText/ instead of the companion repo.
#
# D50 — one interactive instance. A process can survive without a window
# (XWayland / abrupt hide); that still holds the pid lock and makes Start
# look broken. start() recovers those zombies before Popen.

from __future__ import annotations

import os
import shutil
import signal
import subprocess
import sys
import time

_WIN = sys.platform.startswith('win')


def exe_name():
    return 'statghost.exe' if _WIN else 'statghost'


def _is_exe(path):
    if not path:
        return False
    p = os.path.abspath(os.path.expanduser(path))
    if not os.path.isfile(p):
        return False
    if _WIN:
        return True
    return os.access(p, os.X_OK)


def _configured_exe():
    try:
        from . import prefs
    except ImportError:
        try:
            import prefs
        except ImportError:
            return ''
    try:
        return prefs.get_exe()
    except Exception:
        return ''


def _is_under(child, ancestor):
    """True if *child* lives inside *ancestor* (Windows-safe, case folding)."""
    try:
        c = os.path.normcase(os.path.abspath(child))
        a = os.path.normcase(os.path.abspath(ancestor))
        return os.path.commonpath([c, a]) == a
    except ValueError:
        return False


def _looks_like_editor_root(path):
    """True if *path* is the CudaText tree (app/py or the binary)."""
    if not path:
        return False
    return (
        os.path.isdir(os.path.join(path, 'app', 'py'))
        or os.path.isfile(os.path.join(path, 'app', 'cudatext.exe'))
        or os.path.isfile(os.path.join(path, 'app', 'cudatext'))
    )


def sibling_dir(name):
    """Walk up from this file until a sibling directory *name* exists.

    realpath() so a CudaText symlink install still starts in this repo.
    Depth is not hardcoded — survives plugins/<host>/ nesting.

    Skip a candidate that *contains this file*: on Windows, plugins/cudatext
    matches sibling name CudaText (case-insensitive) and is the host folder.

    Win clone `Github/CudaText/CudaText/app` — unwrap one same-named child
    when the sibling itself is only a wrapper (no app/py).
    """
    here = os.path.dirname(os.path.realpath(__file__))
    cur = here
    for _ in range(8):
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cand = os.path.join(parent, name)
        if os.path.isdir(cand) and not _is_under(here, cand):
            path = os.path.abspath(cand)
            if name.lower() == 'cudatext' and not _looks_like_editor_root(path):
                inner = os.path.join(path, 'CudaText')
                if os.path.isdir(inner) and _looks_like_editor_root(inner):
                    return os.path.abspath(inner)
            return path
        cur = parent
    return None


def _sibling_exe():
    """Companion repo → sibling statghost/src/_out/<exe>."""
    root = sibling_dir('statghost')
    if not root:
        return ''
    return os.path.join(root, 'src', '_out', exe_name())


def find_exe(ignore_ini=False):
    if not ignore_ini:
        cfg = _configured_exe()
        if _is_exe(cfg):
            return os.path.abspath(os.path.expanduser(cfg))
    env = (os.environ.get('STATGHOST_EXE') or '').strip()
    if _is_exe(env):
        return os.path.abspath(os.path.expanduser(env))
    sib = _sibling_exe()
    if _is_exe(sib):
        return sib
    w = shutil.which(exe_name())
    if w and _is_exe(w):
        return w
    return None


def list_pids():
    """PIDs of running STATghost processes (empty if none)."""
    if _WIN:
        try:
            out = subprocess.check_output(
                ['tasklist', '/FI', 'IMAGENAME eq ' + exe_name(), '/NH'],
                stderr=subprocess.DEVNULL,
                text=True,
                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0),
            )
        except (OSError, subprocess.CalledProcessError):
            return []
        pids = []
        for line in out.splitlines():
            if exe_name().lower() not in line.lower():
                continue
            parts = line.split()
            for p in parts[1:]:
                if p.isdigit():
                    pids.append(int(p))
                    break
        return pids
    try:
        out = subprocess.check_output(
            ['pgrep', '-x', exe_name()],
            stderr=subprocess.DEVNULL,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return []
    return [int(x) for x in out.split() if x.isdigit()]


def is_running():
    return len(list_pids()) > 0


def _pidfile_path():
    exe = find_exe()
    if not exe:
        return ''
    # Portable/lab: next to binary → data/statghost.pid (uapppaths).
    return os.path.join(os.path.dirname(exe), 'data', 'statghost.pid')


def _clear_pidfile():
    path = _pidfile_path()
    if path and os.path.isfile(path):
        try:
            os.remove(path)
        except OSError:
            pass


def has_app_window():
    """True if a WM window titled STATghost (not the plugin dialog) exists."""
    try:
        out = subprocess.check_output(
            ['wmctrl', '-l'],
            stderr=subprocess.DEVNULL,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        # No wmctrl — cannot tell; assume visible if process exists.
        return is_running()
    for line in out.splitlines():
        # wmctrl -l: id desk host title…
        title = line.split(None, 3)[-1] if line.strip() else ''
        if title.strip() == 'STATghost':
            return True
    return False


def force_stop():
    """SIGTERM then SIGKILL any STATghost; clear D50 pidfile."""
    pids = list_pids()
    for pid in pids:
        try:
            os.kill(pid, signal.SIGTERM)
        except OSError:
            pass
    deadline = time.time() + 2.0
    while time.time() < deadline and list_pids():
        time.sleep(0.05)
    for pid in list_pids():
        try:
            os.kill(pid, signal.SIGKILL)
        except OSError:
            pass
    _clear_pidfile()
    return not is_running()


def start():
    """Launch STATghost detached. One interactive instance (D50).

    Returns (ok, message). If a healthy instance is up, does not Popen.
    If a process exists but has no STATghost window (zombie lock), kills
    it and relaunches.
    """
    if is_running():
        if has_app_window():
            return True, 'already running'
        # Process without window — holding D50 lock; recover.
        force_stop()
        time.sleep(0.2)
    exe = find_exe()
    if not exe:
        cfg = _configured_exe()
        if cfg:
            return False, 'configured path not found — ' + cfg
        return False, (
            'STATghost binary not found — Plugins → STATghost → Config'
        )
    cwd = os.path.dirname(exe)
    try:
        if _WIN:
            flags = 0
            flags |= getattr(subprocess, 'DETACHED_PROCESS', 0)
            flags |= getattr(subprocess, 'CREATE_NEW_PROCESS_GROUP', 0)
            subprocess.Popen(
                [exe], cwd=cwd, close_fds=True, creationflags=flags
            )
        else:
            subprocess.Popen(
                [exe],
                cwd=cwd,
                start_new_session=True,
                close_fds=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
    except OSError as e:
        return False, 'could not start STATghost: ' + str(e)
    for _ in range(40):
        time.sleep(0.05)
        if is_running():
            break
    if not is_running():
        return False, 'started but process exited immediately'
    # Brief wait for the WM title — Wayland/X11 can lag.
    for _ in range(30):
        if has_app_window():
            return True, exe
        time.sleep(0.05)
    return True, exe


def stop_graceful(send_quit_clip):
    """Ask STATghost to Quit via clipboard; force_stop if it hangs.

    send_quit_clip() should put `#. STATGHOST:QUIT <nonce>` on the clipboard.
    """
    if not is_running():
        _clear_pidfile()
        return True, 'not running'
    try:
        send_quit_clip()
    except Exception as e:
        force_stop()
        return True, 'force-stopped after quit error: ' + str(e)
    deadline = time.time() + 3.0
    while time.time() < deadline:
        if not is_running():
            _clear_pidfile()
            return True, 'quit'
        time.sleep(0.1)
    force_stop()
    return True, 'force-stopped (no window / hung Quit)'
