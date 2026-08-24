#include "StatghostIcons.h"
#include "StatghostBridge.h"
#include "StatghostChrome.h"
#include "StatghostTheme.h"

#include <windows.h>
#include <objidl.h>
#include <gdiplus.h>
#include <shlwapi.h>

#include <string>
#include <unordered_map>

#pragma comment(lib, "gdiplus.lib")

namespace
{
    ULONG_PTR g_gdiToken = 0;
    std::unordered_map<std::string, HBITMAP> g_bitmapCache;

    std::wstring iconPathForKey(const char *actionKey, const int sizePx)
    {
        const std::wstring shared = StatghostBridge::sharedResDir();
        if (shared.empty())
            return L"";

        const char *file = StatghostChrome::iconFile(actionKey);
        const std::wstring fileName(file, file + strlen(file));

        const wchar_t *tone = StatghostTheme::iconToneFolder();
        if (wcscmp(tone, L"16px") == 0)
        {
            std::wstring flat = shared + L"\\16px\\" + fileName;
            if (::PathFileExistsW(flat.c_str()))
                return flat;
        }
        else
        {
            std::wstring tonePath = shared + L"\\" + tone + L"\\" + std::to_wstring(sizePx) + L"px\\" + fileName;
            if (::PathFileExistsW(tonePath.c_str()))
                return tonePath;
            tonePath = shared + L"\\" + tone + L"\\" + fileName;
            if (::PathFileExistsW(tonePath.c_str()))
                return tonePath;
        }

        std::wstring flat = shared + L"\\16px\\" + fileName;
        if (::PathFileExistsW(flat.c_str()))
            return flat;

        return shared + L"\\16px\\statghost.png";
    }

    HBITMAP bitmapFromFile(const std::wstring &path, const int sizePx)
    {
        Gdiplus::Bitmap loaded(path.c_str());
        if (loaded.GetLastStatus() != Gdiplus::Ok)
            return nullptr;

        Gdiplus::Bitmap scaled(sizePx, sizePx, PixelFormat32bppARGB);
        Gdiplus::Graphics g(&scaled);
        g.SetInterpolationMode(Gdiplus::InterpolationModeHighQualityBicubic);
        g.DrawImage(&loaded, 0, 0, sizePx, sizePx);

        HBITMAP hbmp = nullptr;
        if (scaled.GetHBITMAP(Gdiplus::Color(0, 0, 0, 0), &hbmp) != Gdiplus::Ok)
            return nullptr;
        return hbmp;
    }
}

void StatghostIcons::init()
{
    if (g_gdiToken == 0)
    {
        Gdiplus::GdiplusStartupInput input;
        Gdiplus::GdiplusStartup(&g_gdiToken, &input, nullptr);
    }
}

void StatghostIcons::shutdown()
{
    clearCache();
    if (g_gdiToken != 0)
    {
        Gdiplus::GdiplusShutdown(g_gdiToken);
        g_gdiToken = 0;
    }
}

void StatghostIcons::clearCache()
{
    for (auto &entry : g_bitmapCache)
    {
        if (entry.second != nullptr)
            ::DeleteObject(entry.second);
    }
    g_bitmapCache.clear();
}

HBITMAP StatghostIcons::loadActionBitmap(const char *actionKey, const int sizePx)
{
    if (actionKey == nullptr)
        return nullptr;

    init();

    const std::string tone = StatghostTheme::darkModeEnabled() ? "white" : "16px";
    const std::string cacheKey = std::string(actionKey) + "@" + std::to_string(sizePx) + tone;
    const auto found = g_bitmapCache.find(cacheKey);
    if (found != g_bitmapCache.end())
        return found->second;

    const std::wstring path = iconPathForKey(actionKey, sizePx);
    HBITMAP bmp = bitmapFromFile(path, sizePx);
    if (bmp != nullptr)
        g_bitmapCache[cacheKey] = bmp;
    return bmp;
}

HICON StatghostIcons::loadActionIcon(const char *actionKey, const int sizePx)
{
    HBITMAP bmp = loadActionBitmap(actionKey, sizePx);
    if (bmp == nullptr)
        return nullptr;

    ICONINFO info = {};
    info.fIcon = TRUE;
    info.hbmColor = bmp;
    info.hbmMask = bmp;
    return ::CreateIconIndirect(&info);
}
