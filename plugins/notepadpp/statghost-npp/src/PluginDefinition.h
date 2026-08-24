#ifndef STATGHOST_PLUGIN_DEFINITION_H
#define STATGHOST_PLUGIN_DEFINITION_H

#include "PluginInterface.h"

const TCHAR NPP_PLUGIN_NAME[] = TEXT("STATghost");

enum StatghostCmdIndex
{
    CMD_ACTION_BASE = 0,
    CMD_PANEL_TOGGLE = 26,
    CMD_CLIPBOARD_PROBE = 27,
    nbFunc = 28
};

void pluginInit(HANDLE hModule);
void pluginCleanUp();
void commandMenuInit();
void commandMenuCleanUp();

bool setCommand(size_t index, TCHAR *cmdName, PFUNCPLUGINCMD pFunc, ShortcutKey *sk = NULL, bool check0nInit = false);

class StatghostPanelDlg;
StatghostPanelDlg *statghostPanelForNotify();
void statghostRegisterPanel();
void statghostOnDarkModeChanged();
HINSTANCE statghostPluginInstance();

#endif
