#include "StatghostConfigDlg.h"

#include "StatghostChrome.h"
#include "StatghostHost.h"
#include "StatghostPanelDlg.h"
#include "StatghostPrefs.h"
#include "PluginDefinition.h"

#include "resource.h"

#include <commdlg.h>
#include <cstring>
#include <string>
#include <vector>

namespace
{
    HWND g_dlg = nullptr;
    HWND g_hostEdit = nullptr;
    HWND g_list = nullptr;
    std::vector<std::string> g_allKeys;

    void populateList()
    {
        if (g_list == nullptr)
            return;

        ::SendMessage(g_list, LB_RESETCONTENT, 0, 0);
        const auto visible = StatghostPrefs::getChromeShow();
        for (const std::string &key : g_allKeys)
        {
            const char *cap = StatghostChrome::menuCaption(key.c_str());
            std::wstring label(cap, cap + strlen(cap));
            const int idx = static_cast<int>(::SendMessageW(g_list, LB_ADDSTRING, 0, reinterpret_cast<LPARAM>(label.c_str())));
            bool on = false;
            for (const std::string &v : visible)
            {
                if (v == key)
                {
                    on = true;
                    break;
                }
            }
            ::SendMessage(g_list, LB_SETSEL, on ? TRUE : FALSE, idx);
        }
    }

    std::vector<std::string> gatherShow()
    {
        std::vector<std::string> out;
        if (g_list == nullptr)
            return out;

        const int count = static_cast<int>(::SendMessage(g_list, LB_GETCOUNT, 0, 0));
        for (int i = 0; i < count; ++i)
        {
            if (::SendMessage(g_list, LB_GETSEL, i, 0) > 0 && i < static_cast<int>(g_allKeys.size()))
                out.push_back(g_allKeys[static_cast<std::size_t>(i)]);
        }
        return out;
    }

    void browseExe()
    {
        if (g_hostEdit == nullptr)
            return;

        wchar_t file[MAX_PATH] = {};
        OPENFILENAMEW ofn = {};
        ofn.lStructSize = sizeof(ofn);
        ofn.hwndOwner = g_dlg;
        ofn.lpstrFilter = L"STATghost\0statghost.exe\0Executables\0*.exe\0All\0*.*\0";
        ofn.lpstrFile = file;
        ofn.nMaxFile = MAX_PATH;
        ofn.Flags = OFN_FILEMUSTEXIST | OFN_PATHMUSTEXIST;
        ofn.lpstrTitle = L"Select statghost.exe";
        if (::GetOpenFileNameW(&ofn))
            ::SetWindowTextW(g_hostEdit, file);
    }

    void saveAndClose(const bool ok)
    {
        if (ok)
        {
            StatghostPrefs::setChromeShow(gatherShow());

            if (g_hostEdit != nullptr)
            {
                wchar_t buf[MAX_PATH] = {};
                ::GetWindowTextW(g_hostEdit, buf, MAX_PATH);
                StatghostPrefs::setHostExe(buf);
            }

            StatghostPrefs::reloadCache();
            if (StatghostPanelDlg *panel = statghostPanelForNotify())
                panel->rebuildGrid();
        }
        ::EndDialog(g_dlg, ok ? IDOK : IDCANCEL);
    }

    INT_PTR CALLBACK configDlgProc(HWND hwnd, UINT message, WPARAM wParam, LPARAM lParam)
    {
        switch (message)
        {
        case WM_INITDIALOG:
            g_dlg = hwnd;
            g_hostEdit = ::GetDlgItem(hwnd, IDC_HOST_EXE);
            g_list = ::GetDlgItem(hwnd, IDC_CHROME_LIST);

            g_allKeys.clear();
            for (std::size_t i = 0; i < StatghostChrome::SHOW_COUNT; ++i)
                g_allKeys.emplace_back(StatghostChrome::showKey(i));

            ::SetWindowTextW(g_hostEdit, StatghostPrefs::getHostExe().c_str());
            {
                const std::wstring found = StatghostHost::findExe();
                if (!found.empty() && StatghostPrefs::getHostExe().empty())
                    ::SetWindowTextW(g_hostEdit, found.c_str());
            }
            populateList();
            ::SetFocus(g_list);
            return FALSE;

        case WM_COMMAND:
            switch (LOWORD(wParam))
            {
            case IDOK:
                saveAndClose(true);
                return TRUE;
            case IDCANCEL:
                saveAndClose(false);
                return TRUE;
            case IDC_HOST_BROWSE:
                browseExe();
                return TRUE;
            }
            break;

        case WM_CLOSE:
            saveAndClose(false);
            return TRUE;
        }
        return FALSE;
    }
}

bool StatghostConfigDlg::showModal(HWND parent)
{
    g_dlg = nullptr;
    g_hostEdit = nullptr;
    g_list = nullptr;
    const INT_PTR rc = ::DialogBoxParamW(
        statghostPluginInstance(),
        MAKEINTRESOURCEW(IDD_STATGHOST_CONFIG),
        parent,
        configDlgProc,
        0);
    return rc == IDOK;
}
