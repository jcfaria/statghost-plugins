#include "StatghostTheme.h"

namespace
{
    NppDarkMode::Colors g_colors;
    bool g_dark = false;
    bool g_haveColors = false;
}

bool StatghostTheme::darkModeEnabled()
{
    return g_dark;
}

NppDarkMode::Colors StatghostTheme::colors()
{
    return g_colors;
}

void StatghostTheme::refresh(const HWND nppHandle)
{
    g_dark = false;
    g_haveColors = false;
    g_colors = NppDarkMode::Colors();

    if (nppHandle == nullptr)
        return;

    g_dark = ::SendMessage(nppHandle, NPPM_ISDARKMODEENABLED, 0, 0) != FALSE;

    NppDarkMode::Colors colors;
    const BOOL ok = ::SendMessage(nppHandle, NPPM_GETDARKMODECOLORS,
                                  sizeof(NppDarkMode::Colors),
                                  reinterpret_cast<LPARAM>(&colors));
    if (ok)
    {
        g_colors = colors;
        g_haveColors = true;
    }
}

COLORREF StatghostTheme::panelBackground()
{
    return g_haveColors ? g_colors.softerBackground : (g_dark ? RGB(30, 30, 30) : RGB(240, 240, 240));
}

COLORREF StatghostTheme::panelText()
{
    return g_haveColors ? g_colors.text : (g_dark ? RGB(220, 220, 220) : RGB(0, 0, 0));
}

COLORREF StatghostTheme::bandBackground()
{
    return g_haveColors ? g_colors.background : (g_dark ? RGB(45, 45, 45) : RGB(225, 225, 225));
}

COLORREF StatghostTheme::cellBackground()
{
    return g_haveColors ? g_colors.pureBackground : (g_dark ? RGB(55, 55, 55) : RGB(255, 255, 255));
}

COLORREF StatghostTheme::cellHotBackground()
{
    return g_haveColors ? g_colors.hotBackground : (g_dark ? RGB(70, 70, 90) : RGB(220, 235, 252));
}

COLORREF StatghostTheme::cellText()
{
    return g_haveColors ? g_colors.darkerText : (g_dark ? RGB(210, 210, 210) : RGB(32, 32, 32));
}

const wchar_t *StatghostTheme::iconToneFolder()
{
    if (g_dark)
        return L"white";
    return L"16px";
}
