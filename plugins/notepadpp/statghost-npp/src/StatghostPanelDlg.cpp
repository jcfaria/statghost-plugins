#include "StatghostPanelDlg.h"

#include "StatghostBridge.h"
#include "StatghostChrome.h"
#include "StatghostCommands.h"
#include "StatghostHost.h"
#include "StatghostIcons.h"
#include "StatghostTheme.h"

namespace
{
    constexpr int kMargin = 6;
    constexpr int kBandHeight = 20;
    constexpr int kCellHeight = 52;
    constexpr int kIconSize = 16;
    constexpr int kIconBtnSize = kIconSize + 4;
    constexpr int kIconTopPad = 2;
    constexpr int kCaptionGap = 2;
    constexpr int kCaptionHeight = 14;
    // CudaText chrome_show.GRID_PANEL_MIN_W — keypad usable below this is cramped.
    constexpr int kMinPanelWidth = 150;
    constexpr int ID_GRID_BASE = 4000;
    constexpr int ID_GRID_CAPTION_BASE = 4500;

    void invokeGridKey(const char *key, StatghostPanelDlg &panel)
    {
        if (key == nullptr)
            return;
        StatghostCommands::invoke(key);
        panel.refreshDynamicCaptions();
    }
}

StatghostPanelDlg::StatghostPanelDlg() : DockingDlgInterface(IDD_STATGHOST_PANEL) {}

void StatghostPanelDlg::destroyGrid()
{
    for (CellControl &cell : _cells)
    {
        if (cell.header != nullptr)
            ::DestroyWindow(cell.header);
        if (cell.button != nullptr)
            ::DestroyWindow(cell.button);
        if (cell.caption != nullptr)
            ::DestroyWindow(cell.caption);
    }
    _cells.clear();
    _btnKeys.clear();
    _gridBuilt = false;
}

void StatghostPanelDlg::rebuildGrid()
{
    destroyGrid();
    if (_hSelf != nullptr)
        buildGrid();
    RECT rc = {};
    ::GetClientRect(_hSelf, &rc);
    layoutGrid(rc.right - rc.left, rc.bottom - rc.top);
}

void StatghostPanelDlg::applyTheme()
{
    for (CellControl &cell : _cells)
    {
        if (cell.header != nullptr)
        {
            ::SetWindowTextW(cell.header, cell.header ? nullptr : nullptr);
        }
    }
}

void StatghostPanelDlg::buildGrid()
{
    if (_gridBuilt || _hSelf == nullptr)
        return;

    const auto plan = StatghostChrome::gridPlan();
    int btnIndex = 0;

    for (const StatghostChrome::GridRow &row : plan)
    {
        if (row.kind == StatghostChrome::GridRowKind::Header)
        {
            CellControl cell;
            cell.header = ::CreateWindowExW(
                0, L"STATIC", row.title.c_str(),
                WS_CHILD | WS_VISIBLE | SS_LEFTNOWORDWRAP,
                kMargin, 0, 100, kBandHeight, _hSelf, nullptr, _hInst, nullptr);
            _cells.push_back(cell);
            continue;
        }

        for (const char *key : row.keys)
        {
            const int ctrlId = ID_GRID_BASE + btnIndex;
            btnIndex += 1;

            std::wstring caption;
            if (key != nullptr && strcmp(key, "arm") == 0)
            {
                caption = StatghostCommands::isArmed() ? L"Armed" : L"Idle";
            }
            else if (key != nullptr && strcmp(key, "host") == 0)
            {
                caption = StatghostHost::isRunning() ? L"Close" : L"Start";
            }
            else
            {
                const char *cap = StatghostChrome::gridCaption(key);
                caption.assign(cap, cap + strlen(cap));
            }

            CellControl cell;
            cell.key = key;
            cell.button = ::CreateWindowExW(
                0, L"BUTTON", L"",
                WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON | BS_BITMAP | BS_CENTER | BS_VCENTER,
                0, 0, kIconBtnSize, kIconBtnSize, _hSelf,
                reinterpret_cast<HMENU>(static_cast<INT_PTR>(ctrlId)), _hInst, nullptr);

            const char *iconKey = key;
            if (key != nullptr && strcmp(key, "arm") == 0)
                iconKey = StatghostCommands::isArmed() ? "armed" : "idle";
            else if (key != nullptr && strcmp(key, "host") == 0)
                iconKey = StatghostHost::isRunning() ? "kill" : "power";

            HBITMAP bmp = StatghostIcons::loadActionBitmap(iconKey, kIconSize);
            if (bmp == nullptr && key != nullptr)
                bmp = StatghostIcons::loadActionBitmap(key, kIconSize);
            if (bmp != nullptr)
                ::SendMessage(cell.button, BM_SETIMAGE, IMAGE_BITMAP, reinterpret_cast<LPARAM>(bmp));

            const int capId = ID_GRID_CAPTION_BASE + (btnIndex - 1);
            cell.caption = ::CreateWindowExW(
                0, L"STATIC", caption.c_str(),
                WS_CHILD | WS_VISIBLE | SS_CENTER | SS_NOTIFY,
                0, 0, 40, kCaptionHeight, _hSelf,
                reinterpret_cast<HMENU>(static_cast<INT_PTR>(capId)), _hInst, nullptr);

            _btnKeys[ctrlId] = key;
            _btnKeys[capId] = key;
            _cells.push_back(cell);
        }

        const size_t pad = StatghostChrome::GRID_COLS - row.keys.size();
        for (size_t p = 0; p < pad; ++p)
        {
            CellControl spacer;
            spacer.caption = ::CreateWindowExW(
                0, L"STATIC", L"",
                WS_CHILD | WS_VISIBLE,
                0, 0, 40, kCellHeight, _hSelf, nullptr, _hInst, nullptr);
            _cells.push_back(spacer);
        }
    }

    _gridBuilt = true;
}

void StatghostPanelDlg::layoutGrid(int width, int height)
{
    if (!_gridBuilt)
        buildGrid();

    const int usableW = width - (kMargin * 2);
    const int cellW = usableW / StatghostChrome::GRID_COLS;
    const int captionYOff = kIconTopPad + kIconBtnSize + kCaptionGap;
    const int captionH = kCellHeight - captionYOff - 2;
    int y = kMargin - _scrollY;
    int rowIndex = 0;

    for (CellControl &cell : _cells)
    {
        if (cell.header != nullptr)
        {
            ::MoveWindow(cell.header, kMargin, y, usableW, kBandHeight, TRUE);
            y += kBandHeight + 2;
            rowIndex = 0;
            continue;
        }

        const int col = rowIndex % StatghostChrome::GRID_COLS;
        const int x = kMargin + col * cellW;
        if (cell.button != nullptr)
        {
            const int iconY = y + kIconTopPad;
            const int captionY = y + captionYOff;
            ::MoveWindow(cell.button, x + (cellW - kIconBtnSize) / 2, iconY, kIconBtnSize, kIconBtnSize, TRUE);
            if (cell.caption != nullptr)
            {
                // Caption band below icon (SS_NOTIFY click); does not overlap the glyph.
                ::MoveWindow(cell.caption, x, captionY, cellW, captionH, TRUE);
            }
        }
        else if (cell.caption != nullptr)
        {
            ::MoveWindow(cell.caption, x, y, cellW, kCellHeight, TRUE);
        }

        rowIndex += 1;
        if (rowIndex % StatghostChrome::GRID_COLS == 0)
            y += kCellHeight;
    }

    _contentHeight = y + _scrollY + kMargin;
    SCROLLINFO si = {};
    si.cbSize = sizeof(si);
    si.fMask = SIF_RANGE | SIF_PAGE | SIF_POS;
    si.nMin = 0;
    si.nMax = _contentHeight;
    si.nPage = static_cast<UINT>(height > 0 ? height : 1);
    si.nPos = _scrollY;
    ::SetScrollInfo(_hSelf, SB_VERT, &si, TRUE);

    const int maxScroll = (_contentHeight > height) ? (_contentHeight - height) : 0;
    if (_scrollY > maxScroll)
    {
        _scrollY = maxScroll;
        layoutGrid(width, height);
    }
}

void StatghostPanelDlg::refreshArmCaption()
{
    for (CellControl &cell : _cells)
    {
        if (cell.key != nullptr && strcmp(cell.key, "arm") == 0)
        {
            if (cell.caption != nullptr)
            {
                const wchar_t *cap = StatghostCommands::isArmed() ? L"Armed" : L"Idle";
                ::SetWindowTextW(cell.caption, cap);
            }
            if (cell.button != nullptr)
            {
                const char *iconKey = StatghostCommands::isArmed() ? "armed" : "idle";
                HBITMAP bmp = StatghostIcons::loadActionBitmap(iconKey, kIconSize);
                if (bmp != nullptr)
                    ::SendMessage(cell.button, BM_SETIMAGE, IMAGE_BITMAP, reinterpret_cast<LPARAM>(bmp));
            }
        }
    }
}

void StatghostPanelDlg::refreshHostCaption()
{
    for (CellControl &cell : _cells)
    {
        if (cell.key != nullptr && strcmp(cell.key, "host") == 0)
        {
            if (cell.caption != nullptr)
            {
                const wchar_t *cap = StatghostHost::isRunning() ? L"Close" : L"Start";
                ::SetWindowTextW(cell.caption, cap);
            }
            if (cell.button != nullptr)
            {
                const char *iconKey = StatghostHost::isRunning() ? "kill" : "power";
                HBITMAP bmp = StatghostIcons::loadActionBitmap(iconKey, kIconSize);
                if (bmp != nullptr)
                    ::SendMessage(cell.button, BM_SETIMAGE, IMAGE_BITMAP, reinterpret_cast<LPARAM>(bmp));
            }
        }
    }
}

void StatghostPanelDlg::refreshDynamicCaptions()
{
    refreshArmCaption();
    refreshHostCaption();
}

INT_PTR CALLBACK StatghostPanelDlg::run_dlgProc(UINT message, WPARAM wParam, LPARAM lParam)
{
    switch (message)
    {
    case WM_INITDIALOG:
        StatghostTheme::refresh(_hParent);
        buildGrid();
        refreshDynamicCaptions();
        return TRUE;

    case WM_SIZE:
        if (wParam != SIZE_MINIMIZED)
            layoutGrid(LOWORD(lParam), HIWORD(lParam));
        return TRUE;

    case WM_VSCROLL:
    {
        SCROLLINFO si = {};
        si.cbSize = sizeof(si);
        si.fMask = SIF_ALL;
        ::GetScrollInfo(_hSelf, SB_VERT, &si);
        const int line = 16;
        int pos = si.nPos;
        switch (LOWORD(wParam))
        {
        case SB_LINEUP:
            pos -= line;
            break;
        case SB_LINEDOWN:
            pos += line;
            break;
        case SB_PAGEUP:
            pos -= static_cast<int>(si.nPage);
            break;
        case SB_PAGEDOWN:
            pos += static_cast<int>(si.nPage);
            break;
        case SB_THUMBTRACK:
            pos = si.nTrackPos;
            break;
        default:
            return TRUE;
        }
        const int maxPos = static_cast<int>(si.nMax - si.nPage);
        if (pos < 0)
            pos = 0;
        if (pos > maxPos)
            pos = maxPos;
        _scrollY = pos;
        RECT rc = {};
        ::GetClientRect(_hSelf, &rc);
        layoutGrid(rc.right - rc.left, rc.bottom - rc.top);
        return TRUE;
    }

    case WM_COMMAND:
    {
        const UINT note = HIWORD(wParam);
        if (note == BN_CLICKED || note == STN_CLICKED)
        {
            const int id = LOWORD(wParam);
            const auto it = _btnKeys.find(id);
            if (it != _btnKeys.end())
                invokeGridKey(it->second, *this);
        }
        return TRUE;
    }

    default:
        break;
    }

    return DockingDlgInterface::run_dlgProc(message, wParam, lParam);
}
