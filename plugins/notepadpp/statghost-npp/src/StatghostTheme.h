#pragma once

#include <windows.h>
#include "Notepad_plus_msgs.h"

namespace NppDarkMode
{
    struct Colors
    {
        COLORREF background = RGB(255, 255, 255);
        COLORREF softerBackground = RGB(240, 240, 240);
        COLORREF hotBackground = RGB(220, 220, 220);
        COLORREF pureBackground = RGB(255, 255, 255);
        COLORREF errorBackground = RGB(255, 200, 200);
        COLORREF text = RGB(0, 0, 0);
        COLORREF darkerText = RGB(64, 64, 64);
        COLORREF disabledText = RGB(128, 128, 128);
        COLORREF linkText = RGB(0, 0, 255);
        COLORREF edge = RGB(200, 200, 200);
        COLORREF hotEdge = RGB(160, 160, 160);
        COLORREF disabledEdge = RGB(220, 220, 220);
    };
}

namespace StatghostTheme
{
    bool darkModeEnabled();
    NppDarkMode::Colors colors();
    COLORREF panelBackground();
    COLORREF panelText();
    COLORREF bandBackground();
    COLORREF cellBackground();
    COLORREF cellHotBackground();
    COLORREF cellText();
    const wchar_t *iconToneFolder();
    void refresh(HWND nppHandle);
}
