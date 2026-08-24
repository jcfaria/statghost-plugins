#pragma once

#include <windows.h>

#include <string>

namespace StatghostIcons
{
    void init();
    void shutdown();
    void clearCache();

    HBITMAP loadActionBitmap(const char *actionKey, int sizePx = 16);
    HICON loadActionIcon(const char *actionKey, int sizePx = 16);
}
