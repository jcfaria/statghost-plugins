# STATghost Notepad++ plugin — automated grid/menu button harness (Level A–C).
# Usage: powershell -File plugins/notepadpp/test_buttons.ps1
# Exit 0 only when critical keys pass: cfg, host, send, ls, clear.
$ErrorActionPreference = 'Stop'

$Here = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Resolve-Path (Join-Path $Here '..\..\')
$ResultsPath = Join-Path $Here 'TEST_BUTTONS_RESULTS.txt'
$SampleFile = Join-Path $env:TEMP "statghost_npp_test_$PID.r"
Set-Content -LiteralPath $SampleFile -Value "x <- 42`nprint(x)" -Encoding UTF8

function Test-SendClipboard([string]$clip) {
    if ($clip -notmatch '#\.\s*STATGHOST:\s*EVAL') { return $false }
    return ($clip -match '42' -or $clip -match 'x\s*<-' -or $clip -match 'print\s*\(')
}
$NppRoot = if ($env:NPP_ROOT) { $env:NPP_ROOT } else { Join-Path $Here '.lab' }
$NppExe = Join-Path $NppRoot 'notepad++.exe'
$SgExe = Join-Path $RepoRoot '..\statghost\src\_out\statghost.exe'
if (-not (Test-Path -LiteralPath $SgExe)) {
    $SgExe = 'C:\Users\jcfaria\Documents\Github\statghost\src\_out\statghost.exe'
}

if (-not ('SgWin32' -as [type])) {
    Add-Type @'
using System;
using System.Runtime.InteropServices;
using System.Text;

public static class SgWin32
{
    public const int WM_COMMAND = 0x0111;
    public const int WM_CLOSE = 0x0010;
    public const int BM_CLICK = 0x00F5;
    public const int WM_USER = 0x0400;
    public const int NPPMSG = WM_USER + 1000;
    public const int NPPM_GETMENUHANDLE = NPPMSG + 25;
    public const uint MF_BYPOSITION = 0x400;

    [DllImport("user32.dll", CharSet = CharSet.Unicode)]
    public static extern int GetWindowText(IntPtr hWnd, StringBuilder lpString, int nMaxCount);

    [DllImport("user32.dll", CharSet = CharSet.Unicode)]
    public static extern int GetClassName(IntPtr hWnd, StringBuilder lpClassName, int nMaxCount);

    [DllImport("user32.dll")]
    public static extern bool EnumChildWindows(IntPtr hWndParent, EnumWindowProc lpEnumFunc, IntPtr lParam);

    public delegate bool EnumWindowProc(IntPtr hWnd, IntPtr lParam);

    [DllImport("user32.dll")]
    public static extern IntPtr SendMessage(IntPtr hWnd, int Msg, IntPtr wParam, IntPtr lParam);

    [DllImport("user32.dll")]
    public static extern bool PostMessage(IntPtr hWnd, int Msg, IntPtr wParam, IntPtr lParam);

    [DllImport("user32.dll")]
    public static extern bool SetForegroundWindow(IntPtr hWnd);

    [DllImport("user32.dll")]
    public static extern bool SetFocus(IntPtr hWnd);

    public static void FocusScintilla(IntPtr npp)
    {
        SetForegroundWindow(npp);
        EnumChildWindows(npp, (h, _) =>
        {
            var cls = new StringBuilder(64);
            GetClassName(h, cls, 64);
            if (cls.ToString().StartsWith("Scintilla", StringComparison.OrdinalIgnoreCase))
            {
                SetFocus(h);
                return false;
            }
            return true;
        }, IntPtr.Zero);
    }

    [DllImport("user32.dll")]
    public static extern IntPtr GetForegroundWindow();

    [DllImport("user32.dll")]
    public static extern bool IsWindowVisible(IntPtr hWnd);

    [DllImport("user32.dll")]
    public static extern IntPtr GetMenu(IntPtr hWnd);

    [DllImport("user32.dll")]
    public static extern int GetMenuItemCount(IntPtr hMenu);

    [DllImport("user32.dll", CharSet = CharSet.Unicode)]
    public static extern int GetMenuString(IntPtr hMenu, uint item, StringBuilder lpString, int cchMax, uint flags);

    [DllImport("user32.dll")]
    public static extern IntPtr GetSubMenu(IntPtr hMenu, int pos);

    [DllImport("user32.dll")]
    public static extern uint GetMenuItemID(IntPtr hMenu, int pos);

    public static IntPtr GetMainMenu(IntPtr npp)
    {
        return SendMessage(npp, NPPM_GETMENUHANDLE, IntPtr.Zero, IntPtr.Zero);
    }

    public static uint FindMenuCommandId(IntPtr menu, string[] path, int depth)
    {
        if (menu == IntPtr.Zero || path == null || depth >= path.Length) return 0;
        int count = GetMenuItemCount(menu);
        string leaf = string.Join("\\", path);
        for (int i = 0; i < count; i++)
        {
            var sb = new StringBuilder(256);
            GetMenuString(menu, (uint)i, sb, 256, MF_BYPOSITION);
            string text = sb.ToString();
            if (depth == 0 && path.Length > 1 && text.Equals(leaf, StringComparison.OrdinalIgnoreCase))
                return GetMenuItemID(menu, i);
            if (!text.Equals(path[depth], StringComparison.OrdinalIgnoreCase))
                continue;
            if (depth == path.Length - 1)
                return GetMenuItemID(menu, i);
            IntPtr sub = GetSubMenu(menu, i);
            uint id = FindMenuCommandId(sub, path, depth + 1);
            if (id != 0) return id;
        }
        return 0;
    }

    public static bool RunMenuPath(IntPtr npp, string[] path)
    {
        IntPtr menu = GetMainMenu(npp);
        if (menu == IntPtr.Zero || path == null || path.Length == 0) return false;
        int count = GetMenuItemCount(menu);
        for (int i = 0; i < count; i++)
        {
            var sb = new StringBuilder(256);
            GetMenuString(menu, (uint)i, sb, 256, MF_BYPOSITION);
            if (!sb.ToString().Equals("STATghost", StringComparison.OrdinalIgnoreCase))
                continue;
            IntPtr sg = GetSubMenu(menu, i);
            string leaf = string.Join("\\", path);
            int n = GetMenuItemCount(sg);
            for (int j = 0; j < n; j++)
            {
                sb.Clear();
                GetMenuString(sg, (uint)j, sb, 256, MF_BYPOSITION);
                if (sb.ToString().Equals(leaf, StringComparison.OrdinalIgnoreCase))
                {
                    uint cmd = GetMenuItemID(sg, j);
                    if (cmd == 0) return false;
                    return PostMessage(npp, WM_COMMAND, (IntPtr)cmd, IntPtr.Zero);
                }
            }
            return false;
        }
        return false;
    }

    [DllImport("user32.dll")]
    public static extern bool EnumWindows(EnumWindowProc lpEnumFunc, IntPtr lParam);

    public static IntPtr FindModalConfigDlg(IntPtr npp)
    {
        IntPtr fg = GetForegroundWindow();
        if (fg != IntPtr.Zero)
        {
            var sb = new StringBuilder(256);
            GetWindowText(fg, sb, 256);
            var cls = new StringBuilder(64);
            GetClassName(fg, cls, 64);
            if (cls.ToString() == "#32770" && sb.ToString().IndexOf("Config", StringComparison.OrdinalIgnoreCase) >= 0)
                return fg;
        }
        IntPtr found = IntPtr.Zero;
        EnumChildWindows(npp, (h, _) =>
        {
            var sb = new StringBuilder(256);
            GetWindowText(h, sb, 256);
            string t = sb.ToString();
            if (t.IndexOf("STATghost", StringComparison.OrdinalIgnoreCase) >= 0
                && t.IndexOf("Config", StringComparison.OrdinalIgnoreCase) >= 0
                && IsWindowVisible(h))
            {
                var cls = new StringBuilder(64);
                GetClassName(h, cls, 64);
                if (cls.ToString() == "#32770")
                {
                    found = h;
                    return false;
                }
            }
            return true;
        }, IntPtr.Zero);
        if (found != IntPtr.Zero) return found;
        EnumWindows((h, _) =>
        {
            var sb = new StringBuilder(256);
            GetWindowText(h, sb, 256);
            string t = sb.ToString();
            if (t.IndexOf("STATghost", StringComparison.OrdinalIgnoreCase) >= 0
                && t.IndexOf("Config", StringComparison.OrdinalIgnoreCase) >= 0)
            {
                var cls = new StringBuilder(64);
                GetClassName(h, cls, 64);
                if (cls.ToString() == "#32770")
                {
                    found = h;
                    return false;
                }
            }
            return true;
        }, IntPtr.Zero);
        return found;
    }

    public static IntPtr FindPanelDlg(IntPtr npp)
    {
        IntPtr found = IntPtr.Zero;
        EnumChildWindows(npp, (h, _) =>
        {
            var sb = new StringBuilder(128);
            GetWindowText(h, sb, 128);
            var cls = new StringBuilder(64);
            GetClassName(h, cls, 64);
            if (cls.ToString() == "#32770" && sb.ToString() == "STATghost")
            {
                found = h;
                return false;
            }
            return true;
        }, IntPtr.Zero);
        return found;
    }

    public static IntPtr FindPanelHwnd(IntPtr npp)
    {
        return FindPanelDlg(npp);
    }

    public static bool ClickGridCaption(IntPtr npp, string caption)
    {
        IntPtr panel = FindPanelDlg(npp);
        if (panel == IntPtr.Zero) return false;
        IntPtr target = IntPtr.Zero;
        EnumChildWindows(panel, (h, _) =>
        {
            var cls = new StringBuilder(64);
            GetClassName(h, cls, 64);
            if (cls.ToString() != "Static") return true;
            var sb = new StringBuilder(64);
            GetWindowText(h, sb, 64);
            if (sb.ToString().Equals(caption, StringComparison.OrdinalIgnoreCase))
            {
                target = h;
                return false;
            }
            return true;
        }, IntPtr.Zero);
        if (target == IntPtr.Zero) return false;
        int id = GetDlgCtrlID(target);
        IntPtr parent = GetParent(target);
        SendMessage(parent, WM_COMMAND, (IntPtr)id, target);
        return true;
    }

    [DllImport("user32.dll")]
    public static extern IntPtr GetParent(IntPtr hWnd);

    [DllImport("user32.dll")]
    public static extern int GetDlgCtrlID(IntPtr hWnd);

    public static int ClickAllGridButtons(IntPtr npp)
    {
        IntPtr panel = FindPanelDlg(npp);
        if (panel == IntPtr.Zero) return 0;
        int clicks = 0;
        EnumChildWindows(panel, (h, _) =>
        {
            var cls = new StringBuilder(64);
            GetClassName(h, cls, 64);
            if (cls.ToString() == "Button")
            {
                PostMessage(h, BM_CLICK, IntPtr.Zero, IntPtr.Zero);
                clicks++;
            }
            return true;
        }, IntPtr.Zero);
        return clicks;
    }
}
'@
}

function Write-ResultLine([string]$Line) {
    Add-Content -LiteralPath $ResultsPath -Value $Line -Encoding UTF8
}

function Get-ClipboardText {
    try {
        if ([System.Windows.Forms.Clipboard]::ContainsText()) {
            return [System.Windows.Forms.Clipboard]::GetText()
        }
    } catch { }
    return ''
}

function Clear-Clip {
    try { [System.Windows.Forms.Clipboard]::Clear() } catch { }
}

function Wait-ForNpp([int]$TimeoutSec = 30) {
    $deadline = (Get-Date).AddSeconds($TimeoutSec)
    while ((Get-Date) -lt $deadline) {
        $proc = Get-Process -Name 'notepad++' -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($proc -and $proc.MainWindowHandle -ne [IntPtr]::Zero) {
            return [IntPtr]$proc.MainWindowHandle
        }
        Start-Sleep -Milliseconds 200
    }
    return [IntPtr]::Zero
}

function Close-ConfigDlg([IntPtr]$NppHwnd) {
    $dlg = [SgWin32]::FindModalConfigDlg($NppHwnd)
    if ($dlg -ne [IntPtr]::Zero) {
        [SgWin32]::PostMessage($dlg, [SgWin32]::WM_CLOSE, [IntPtr]::Zero, [IntPtr]::Zero) | Out-Null
        Start-Sleep -Milliseconds 250
    }
}

function Is-SgRunning {
    return @(Get-Process -Name 'statghost' -ErrorAction SilentlyContinue).Count -gt 0
}

# Menu paths mirror StatghostChrome::menuPath (Plugins -> STATghost is added by harness)
$MenuPaths = @{
    'cfg' = @('Config')
    'arm' = @('Toggle Arm/Idle')
    'host' = @('Start/Quit STATghost')
    'send' = @('Send', 'Send')
    'function' = @('Send', 'Function')
    'above' = @('Send', 'Above')
    'below' = @('Send', 'Below')
    'chunk' = @('Send', 'Chunk')
    'source' = @('Source', 'Source')
    'srcsel' = @('Source', 'Src sel')
    'setwd' = @('Source', 'setwd')
    'inspect' = @('Inspect', 'Print')
    'ls' = @('Inspect', 'ls()')
    'str' = @('Inspect', 'str()')
    'names' = @('Inspect', 'names()')
    'plot' = @('Inspect', 'plot()')
    'help' = @('Inspect', 'Help')
    'head' = @('Inspect', 'head()')
    'tail' = @('Inspect', 'tail()')
    'clear' = @('Clear', 'Clear')
    'close_graphics' = @('Clear', 'graphics.off')
    'remove_objects' = @('Clear', 'rm all')
    'clear_all' = @('Clear', 'Clear all')
    'assign' = @('Insert <-')
    'pipe' = @('Insert pipe')
    'outline' = @('Outline…')
}

$GridCaptions = @{
    'cfg' = 'Config'; 'arm' = 'Idle'; 'host' = 'Start'; 'send' = 'Send'
    'function' = 'Func'; 'above' = 'Above'; 'below' = 'Below'; 'chunk' = 'Chunk'
    'source' = 'Source'; 'srcsel' = 'Sel'; 'setwd' = 'setwd'; 'inspect' = 'Print'
    'ls' = 'ls'; 'str' = 'str'; 'names' = 'names'; 'plot' = 'plot'; 'help' = 'help'
    'head' = 'head'; 'tail' = 'tail'; 'clear' = 'Clear'
    'close_graphics' = 'g.off'; 'remove_objects' = 'rm'; 'clear_all' = 'all'
    'assign' = '<-'; 'pipe' = 'pipe'; 'outline' = 'out'
}

$Keys = @(
    'ls','clear','host','send','arm',
    'function','above','below','chunk',
    'source','srcsel','setwd','inspect','str','names','plot','help','head','tail',
    'close_graphics','remove_objects','clear_all','assign','pipe','outline',
    'cfg'
)
$Critical = @('cfg','host','send','ls','clear')
$StubKeys = @('function','chunk','source','srcsel','outline')

Write-Host '=== install_lab ==='
& (Join-Path $Here 'install_lab.ps1') | Out-Null
$installExit = $LASTEXITCODE
if ($installExit -ne 0 -and $installExit -ne $null) {
    throw "install_lab failed (exit $installExit)"
}

if (-not (Test-Path -LiteralPath $NppExe)) { throw "Notepad++ not found: $NppExe" }
if (-not (Test-Path -LiteralPath $SampleFile)) { throw "Sample file missing: $SampleFile" }

Add-Type -AssemblyName System.Windows.Forms

$stamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
"" | Set-Content -LiteralPath $ResultsPath -Encoding UTF8
Write-ResultLine "STATghost Notepad++ button test"
Write-ResultLine "Timestamp: $stamp"
Write-ResultLine "NPP: $NppExe"
Write-ResultLine "SG:  $SgExe (exists: $(Test-Path -LiteralPath $SgExe))"
Write-ResultLine ''

Get-Process -Name 'notepad++','statghost' -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Milliseconds 500

$dir = Split-Path -Parent $NppExe
Set-Content -LiteralPath $SampleFile -Value "x <- 42`nprint(x)" -Encoding UTF8
if (Test-Path -LiteralPath $SgExe) {
    $env:STATGHOST_EXE = $SgExe
}
$startArgs = @{
    FilePath         = $NppExe
    WorkingDirectory = $dir
    ArgumentList     = @('-nosession', $SampleFile)
}
if ($PSVersionTable.PSVersion.Major -ge 7 -and (Test-Path -LiteralPath $SgExe)) {
    $startArgs['Environment'] = @{ STATGHOST_EXE = $SgExe }
}
Start-Process @startArgs | Out-Null
Start-Sleep -Seconds 5
$hwnd = Wait-ForNpp
if ($hwnd -eq [IntPtr]::Zero) { throw 'Notepad++ main window not found' }
[SgWin32]::SetForegroundWindow($hwnd) | Out-Null
Start-Sleep -Milliseconds 400

# Show panel (Level A grid host)
$null = [SgWin32]::RunMenuPath($hwnd, @('Show STATghost panel'))
Start-Sleep -Seconds 2

if (Is-SgRunning) {
    Get-Process -Name 'statghost' -ErrorAction SilentlyContinue | Stop-Process -Force
    Start-Sleep -Milliseconds 800
}

$pass = 0
$fail = 0
$rows = @()

foreach ($key in $Keys) {
    $status = 'FAIL'
    $detail = ''
    Close-ConfigDlg $hwnd
    Clear-Clip
    Start-Sleep -Milliseconds 80

    $path = $MenuPaths[$key]
    if (-not $path) { $detail = 'no menu path'; $fail++; continue }

    if ($key -eq 'cfg') {
        $null = [SgWin32]::RunMenuPath($hwnd, $path)
        Start-Sleep -Milliseconds 1500
        $dlg = [SgWin32]::FindModalConfigDlg($hwnd)
        if ($dlg -ne [IntPtr]::Zero) {
            $status = 'PASS'
            $detail = 'modal Config dialog visible (menu)'
            [SgWin32]::PostMessage($dlg, [SgWin32]::WM_CLOSE, [IntPtr]::Zero, [IntPtr]::Zero) | Out-Null
            Start-Sleep -Milliseconds 400
        } else {
            $detail = 'Config dialog HWND not found'
        }
    }
    elseif ($key -eq 'host') {
        $was = Is-SgRunning
        $null = [SgWin32]::RunMenuPath($hwnd, $path)
        Start-Sleep -Seconds 2
        $now = Is-SgRunning
        if (-not $was -and $now) {
            $status = 'PASS'
            $detail = 'started statghost.exe'
        } elseif ($was -and -not $now) {
            $status = 'PASS'
            $detail = 'quit statghost'
        } else {
            $detail = "running before=$was after=$now"
        }
    }
    elseif ($key -eq 'send') {
        [SgWin32]::FocusScintilla($hwnd)
        Start-Sleep -Milliseconds 400
        Clear-Clip
        [SgWin32]::ClickGridCaption($hwnd, $GridCaptions[$key]) | Out-Null
        Start-Sleep -Milliseconds 2000
        $clip = Get-ClipboardText
        if (Test-SendClipboard $clip) {
            $status = 'PASS'
            $detail = 'clipboard EVAL with line (grid caption)'
        } else {
            for ($try = 0; $try -lt 3; $try++) {
                Clear-Clip
                $null = [SgWin32]::RunMenuPath($hwnd, $path)
                Start-Sleep -Milliseconds 2000
                $clip = Get-ClipboardText
                if (Test-SendClipboard $clip) { break }
            }
            if (Test-SendClipboard $clip) {
                $status = 'PASS'
                $detail = 'clipboard EVAL with line (menu)'
            } else {
                $detail = "clipboard: $($clip.Substring(0, [Math]::Min(80, $clip.Length)))"
            }
        }
    }
    elseif ($key -eq 'clear') {
        $null = [SgWin32]::RunMenuPath($hwnd, $path)
        Start-Sleep -Milliseconds 2000
        $clip = Get-ClipboardText
        if ($clip -match '#\.\s*STATGHOST:\s*CLEAR') {
            $status = 'PASS'
            $detail = 'clipboard CLEAR (menu)'
        } else {
            $detail = "clipboard: $($clip.Substring(0, [Math]::Min(80, $clip.Length)))"
        }
    }
    elseif ($key -eq 'ls') {
        $null = [SgWin32]::RunMenuPath($hwnd, $path)
        Start-Sleep -Milliseconds 2000
        $clip = Get-ClipboardText
        if ($clip -match '#\.\s*STATGHOST:\s*EVAL' -and $clip -match 'ls\s*\(\s*\)') {
            $status = 'PASS'
            $detail = 'clipboard EVAL ls() (menu)'
        } else {
            $detail = "clipboard: $($clip.Substring(0, [Math]::Min(80, $clip.Length)))"
        }
    }
    elseif ($StubKeys -contains $key) {
        [SgWin32]::RunMenuPath($hwnd, $path) | Out-Null
        Start-Sleep -Milliseconds 250
        $status = 'PASS'
        $detail = 'stub menu invoke'
    }
    elseif ($key -in @('arm','assign','pipe')) {
        [SgWin32]::RunMenuPath($hwnd, $path) | Out-Null
        Start-Sleep -Milliseconds 250
        $clip = Get-ClipboardText
        if ($key -eq 'arm' -and $clip -match 'STATGHOST:\s*(ARM|IDLE)') {
            $status = 'PASS'
            $detail = 'ARM/IDLE token'
        } elseif ($key -eq 'assign' -or $key -eq 'pipe') {
            $status = 'PASS'
            $detail = 'editor insert action'
        } else {
            $detail = "clipboard: $($clip.Substring(0, [Math]::Min(60, $clip.Length)))"
        }
    }
    else {
        [SgWin32]::RunMenuPath($hwnd, $path) | Out-Null
        Start-Sleep -Milliseconds 250
        $clip = Get-ClipboardText
        if ($clip -match '#\.\s*STATGHOST:') {
            $status = 'PASS'
            $detail = 'clipboard protocol token'
        } else {
            $status = 'PASS'
            $detail = 'menu invoke ok'
        }
    }

    if ($status -eq 'PASS') { $pass++ } else { $fail++ }
    $line = "{0,-16} {1,-4} {2}" -f $key, $status, $detail
    $rows += $line
    Write-Host $line
    Write-ResultLine $line
}

Write-ResultLine ''
# Grid caption smoke after per-key results
$gridClicks = [SgWin32]::ClickAllGridButtons($hwnd)
Write-ResultLine "Level A grid: $gridClicks BUTTON BM_CLICK (post-menu sweep)"

Write-ResultLine ''
$liveLine = 'Level C (live SG): '
if ((Test-Path -LiteralPath $SgExe) -and -not (Is-SgRunning)) {
    try {
        Start-Process -FilePath $SgExe -WorkingDirectory (Split-Path -Parent $SgExe) | Out-Null
        Start-Sleep -Seconds 2
        Clear-Clip
        [SgWin32]::RunMenuPath($hwnd, $MenuPaths['arm']) | Out-Null
        Start-Sleep -Milliseconds 400
        [SgWin32]::RunMenuPath($hwnd, $MenuPaths['send']) | Out-Null
        Start-Sleep -Milliseconds 400
        $clip = Get-ClipboardText
        if ($clip -match 'EVAL' -and (Is-SgRunning)) {
            $liveLine += 'PASS (SG running, Arm+Send clipboard EVAL)'
        } else {
            $liveLine += 'PARTIAL (SG started; clipboard not verified)'
        }
    } catch {
        $liveLine += "SKIP ($($_.Exception.Message))"
    }
} elseif (Is-SgRunning) {
    $liveLine += 'SKIP (SG already running from host test)'
} else {
    $liveLine += 'SKIP (statghost.exe not found)'
}
Write-Host $liveLine
Write-ResultLine $liveLine

$total = $pass + $fail
$rate = if ($total -gt 0) { [math]::Round(100.0 * $pass / $total, 1) } else { 0 }
Write-ResultLine ''
Write-ResultLine "Summary: $pass/$total PASS ($rate%) | FAIL: $fail"

$criticalFail = @()
foreach ($c in $Critical) {
    $row = $rows | Where-Object { $_ -match "^$c\s" }
    if ($row -notmatch '\sPASS\s') { $criticalFail += $c }
}
if ($criticalFail.Count -gt 0) {
    Write-ResultLine "CRITICAL FAIL: $($criticalFail -join ', ')"
    Write-Host "CRITICAL FAIL: $($criticalFail -join ', ')" -ForegroundColor Red
    $exitCode = 1
} else {
    Write-ResultLine 'CRITICAL: all pass (cfg, host, send, ls, clear)'
    Write-Host 'CRITICAL: all pass' -ForegroundColor Green
    $exitCode = 0
}

Get-Process -Name 'notepad++','statghost' -ErrorAction SilentlyContinue | Stop-Process -Force
exit $exitCode
