#include "PluginDefinition.h"

#include "StatghostBridge.h"
#include "StatghostChrome.h"
#include "StatghostCommands.h"
#include "StatghostIcons.h"
#include "StatghostPrefs.h"
#include "StatghostPanelDlg.h"
#include "StatghostTheme.h"

namespace
{
    // Lab automation — NPPM_MSGTOPLUGIN → messageProc(internalMsg, …)
    constexpr UINT SG_TEST_SHOW_PANEL = 0x5347;
    constexpr UINT SG_TEST_INVOKE_INDEX = 0x5348;
}

extern FuncItem funcItem[nbFunc];
extern NppData nppData;

BOOL APIENTRY DllMain(HANDLE hModule, DWORD reasonForCall, LPVOID /*lpReserved*/)
{
    switch (reasonForCall)
    {
    case DLL_PROCESS_ATTACH:
        pluginInit(hModule);
        break;

    case DLL_PROCESS_DETACH:
        pluginCleanUp();
        break;

    default:
        break;
    }

    return TRUE;
}

extern "C" __declspec(dllexport) void setInfo(NppData notepadPlusData)
{
    nppData = notepadPlusData;
    StatghostBridge::init(&nppData);
    StatghostPrefs::reloadCache();
    StatghostTheme::refresh(nppData._nppHandle);
    commandMenuInit();
}

extern "C" __declspec(dllexport) const TCHAR *getName()
{
    return NPP_PLUGIN_NAME;
}

extern "C" __declspec(dllexport) FuncItem *getFuncsArray(int *nbF)
{
    *nbF = nbFunc;
    return funcItem;
}

extern "C" __declspec(dllexport) void beNotified(SCNotification *notifyCode)
{
    switch (notifyCode->nmhdr.code)
    {
    case NPPN_READY:
        StatghostTheme::refresh(nppData._nppHandle);
        statghostRegisterPanel();
        break;

    case NPPN_DARKMODECHANGED:
        statghostOnDarkModeChanged();
        break;

    case NPPN_SHUTDOWN:
        commandMenuCleanUp();
        break;

    default:
        break;
    }
}

extern "C" __declspec(dllexport) LRESULT messageProc(UINT Message, WPARAM wParam, LPARAM /*lParam*/)
{
    switch (Message)
    {
    case SG_TEST_SHOW_PANEL:
        statghostRegisterPanel();
        if (StatghostPanelDlg *panel = statghostPanelForNotify())
            panel->display();
        return TRUE;

    case SG_TEST_INVOKE_INDEX:
        if (wParam < StatghostChrome::SHOW_COUNT)
        {
            StatghostCommands::invokeByShowIndex(static_cast<std::size_t>(wParam));
            if (StatghostPanelDlg *panel = statghostPanelForNotify())
                panel->refreshDynamicCaptions();
        }
        return TRUE;

    default:
        break;
    }
    return TRUE;
}

extern "C" __declspec(dllexport) BOOL isUnicode()
{
    return TRUE;
}
