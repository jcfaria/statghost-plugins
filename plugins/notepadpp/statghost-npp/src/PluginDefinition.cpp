#include "PluginDefinition.h"

#include "StatghostBridge.h"
#include "StatghostChrome.h"
#include "StatghostCommands.h"
#include "StatghostIcons.h"
#include "StatghostPanelDlg.h"
#include "StatghostProtocol.h"
#include "StatghostTheme.h"

#include <cstring>
#include <string>

FuncItem funcItem[nbFunc];
NppData nppData;

namespace
{
    StatghostPanelDlg g_panel;
    bool g_panelRegistered = false;
    HINSTANCE g_pluginInst = nullptr;
    wchar_t g_menuNames[StatghostChrome::SHOW_COUNT][96] = {};

#define SG_MENU_DISPATCH(n)                          \
    static void sg_menu_dispatch_##n()               \
    {                                                \
        StatghostCommands::invokeByShowIndex(n);      \
        g_panel.refreshDynamicCaptions();            \
    }

    SG_MENU_DISPATCH(0)
    SG_MENU_DISPATCH(1)
    SG_MENU_DISPATCH(2)
    SG_MENU_DISPATCH(3)
    SG_MENU_DISPATCH(4)
    SG_MENU_DISPATCH(5)
    SG_MENU_DISPATCH(6)
    SG_MENU_DISPATCH(7)
    SG_MENU_DISPATCH(8)
    SG_MENU_DISPATCH(9)
    SG_MENU_DISPATCH(10)
    SG_MENU_DISPATCH(11)
    SG_MENU_DISPATCH(12)
    SG_MENU_DISPATCH(13)
    SG_MENU_DISPATCH(14)
    SG_MENU_DISPATCH(15)
    SG_MENU_DISPATCH(16)
    SG_MENU_DISPATCH(17)
    SG_MENU_DISPATCH(18)
    SG_MENU_DISPATCH(19)
    SG_MENU_DISPATCH(20)
    SG_MENU_DISPATCH(21)
    SG_MENU_DISPATCH(22)
    SG_MENU_DISPATCH(23)
    SG_MENU_DISPATCH(24)
    SG_MENU_DISPATCH(25)

    static PFUNCPLUGINCMD sg_menu_funcs[] = {
        sg_menu_dispatch_0, sg_menu_dispatch_1, sg_menu_dispatch_2, sg_menu_dispatch_3,
        sg_menu_dispatch_4, sg_menu_dispatch_5, sg_menu_dispatch_6, sg_menu_dispatch_7,
        sg_menu_dispatch_8, sg_menu_dispatch_9, sg_menu_dispatch_10, sg_menu_dispatch_11,
        sg_menu_dispatch_12, sg_menu_dispatch_13, sg_menu_dispatch_14, sg_menu_dispatch_15,
        sg_menu_dispatch_16, sg_menu_dispatch_17, sg_menu_dispatch_18, sg_menu_dispatch_19,
        sg_menu_dispatch_20, sg_menu_dispatch_21, sg_menu_dispatch_22, sg_menu_dispatch_23,
        sg_menu_dispatch_24, sg_menu_dispatch_25,
    };

    void registerPanel()
    {
        if (g_panelRegistered)
            return;

        g_panel.setParent(nppData._nppHandle);
        tTbData data = {};
        g_panel.create(&data);

        data.uMask = DWS_DF_CONT_RIGHT;
        data.pszModuleName = g_panel.getPluginFileName();
        data.dlgID = CMD_PANEL_TOGGLE;

        ::SendMessage(nppData._nppHandle, NPPM_DMMREGASDCKDLG, 0, reinterpret_cast<LPARAM>(&data));
        g_panelRegistered = true;
    }

    void cmdPanelToggle()
    {
        registerPanel();
        g_panel.display();
    }

    void cmdClipboardProbe()
    {
        if (!::OpenClipboard(nullptr))
        {
            StatghostBridge::setStatusMessage(L"STATghost: clipboard open failed");
            return;
        }

        std::wstring clip;
        HANDLE data = ::GetClipboardData(CF_UNICODETEXT);
        if (data != nullptr)
        {
            const wchar_t *raw = static_cast<const wchar_t *>(::GlobalLock(data));
            if (raw != nullptr)
            {
                clip = raw;
                ::GlobalUnlock(data);
            }
        }
        ::CloseClipboard();

        std::wstring message = L"STATghost: clipboard ";
        if (clip.empty())
            message += L"empty";
        else
        {
            const size_t previewLen = clip.size() > 64 ? 64 : clip.size();
            message += L"\"";
            message.append(clip, 0, previewLen);
            if (clip.size() > previewLen)
                message += L"...";
            message += L"\"";
        }
        StatghostBridge::setStatusMessage(message);
    }
}

void pluginInit(HANDLE hModule)
{
    g_pluginInst = static_cast<HINSTANCE>(hModule);
    g_panel.init(g_pluginInst, nullptr);
    StatghostBridge::init(&nppData);
    commandMenuInit();
    StatghostTheme::refresh(nppData._nppHandle);
    StatghostIcons::init();
}

void pluginCleanUp()
{
    StatghostIcons::shutdown();
}

void commandMenuInit()
{
    for (std::size_t i = 0; i < StatghostChrome::SHOW_COUNT; ++i)
    {
        const char *key = StatghostChrome::showKey(i);
        const std::wstring path = StatghostChrome::menuPath(key);
        wcscpy_s(g_menuNames[i], path.c_str());
        setCommand(static_cast<size_t>(i), g_menuNames[i], sg_menu_funcs[i], nullptr, false);
    }

    setCommand(CMD_PANEL_TOGGLE, TEXT("Show STATghost panel"), cmdPanelToggle, nullptr, false);
    setCommand(CMD_CLIPBOARD_PROBE, TEXT("Clipboard probe"), cmdClipboardProbe, nullptr, false);
}

void commandMenuCleanUp()
{
}

bool setCommand(size_t index, TCHAR *cmdName, PFUNCPLUGINCMD pFunc, ShortcutKey *sk, bool check0nInit)
{
    if (index >= nbFunc || pFunc == nullptr)
        return false;

    lstrcpy(funcItem[index]._itemName, cmdName);
    funcItem[index]._pFunc = pFunc;
    funcItem[index]._init2Check = check0nInit;
    funcItem[index]._pShKey = sk;
    return true;
}

StatghostPanelDlg *statghostPanelForNotify()
{
    return &g_panel;
}

void statghostRegisterPanel()
{
    registerPanel();
}

void statghostOnDarkModeChanged()
{
    StatghostTheme::refresh(nppData._nppHandle);
    StatghostIcons::clearCache();
    g_panel.rebuildGrid();
}

HINSTANCE statghostPluginInstance()
{
    return g_pluginInst;
}
