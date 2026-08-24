#include "StatghostPrefs.h"
#include "StatghostBridge.h"
#include "StatghostChrome.h"
#include "PluginInterface.h"

#include <shlobj.h>
#include <shlwapi.h>

#include <cstring>
#include <unordered_set>

namespace
{
    std::vector<std::string> g_chromeShowCache;
    bool g_cacheLoaded = false;

    std::wstring queryNppConfigDir()
    {
        HWND npp = StatghostBridge::nppHandle();
        if (npp == nullptr)
            return L"";

        const int len = static_cast<int>(::SendMessage(npp, NPPM_GETPLUGINSCONFIGDIR, 0, 0));
        if (len <= 0)
            return L"";

        std::wstring buf(static_cast<std::size_t>(len) + 1, L'\0');
        ::SendMessage(npp, NPPM_GETPLUGINSCONFIGDIR, static_cast<WPARAM>(len + 1),
                      reinterpret_cast<LPARAM>(buf.data()));
        buf.resize(static_cast<std::size_t>(len));
        return buf;
    }

    std::wstring readIniString(const wchar_t *section, const wchar_t *key, const wchar_t *fallback)
    {
        const std::wstring path = StatghostPrefs::iniPath();
        if (path.empty())
            return fallback ? fallback : L"";

        wchar_t buf[4096] = {};
        ::GetPrivateProfileStringW(section, key, fallback, buf, static_cast<DWORD>(std::size(buf)), path.c_str());
        return buf;
    }

    void writeIniString(const wchar_t *section, const wchar_t *key, const wchar_t *value)
    {
        const std::wstring path = StatghostPrefs::iniPath();
        if (path.empty())
            return;

        wchar_t dir[MAX_PATH] = {};
        wcscpy_s(dir, path.c_str());
        ::PathRemoveFileSpecW(dir);
        ::SHCreateDirectoryExW(nullptr, dir, nullptr);
        ::WritePrivateProfileStringW(section, key, value, path.c_str());
    }

    std::vector<std::string> defaultShowKeys()
    {
        std::vector<std::string> keys;
        for (std::size_t i = 0; i < StatghostChrome::SHOW_COUNT; ++i)
            keys.emplace_back(StatghostChrome::showKey(i));
        return keys;
    }

    std::vector<std::string> parseShowCsv(const std::wstring &raw)
    {
        if (raw.empty())
            return defaultShowKeys();

        std::vector<std::string> out;
        std::unordered_set<std::string> seen;
        std::wstring token;
        for (const wchar_t ch : raw)
        {
            if (ch == L',' || ch == L';' || ch == L' ' || ch == L'\t' || ch == L'\r' || ch == L'\n')
            {
                if (!token.empty())
                {
                    const int need = ::WideCharToMultiByte(CP_UTF8, 0, token.c_str(), -1, nullptr, 0, nullptr, nullptr);
                    if (need > 0)
                    {
                        std::string key(static_cast<std::size_t>(need), '\0');
                        ::WideCharToMultiByte(CP_UTF8, 0, token.c_str(), -1, key.data(), need, nullptr, nullptr);
                        if (!key.empty() && key.back() == '\0')
                            key.pop_back();
                        if (!key.empty() && seen.insert(key).second)
                            out.push_back(key);
                    }
                    token.clear();
                }
                continue;
            }
            token += ch;
        }
        if (!token.empty())
        {
            const int need = ::WideCharToMultiByte(CP_UTF8, 0, token.c_str(), -1, nullptr, 0, nullptr, nullptr);
            if (need > 0)
            {
                std::string key(static_cast<std::size_t>(need), '\0');
                ::WideCharToMultiByte(CP_UTF8, 0, token.c_str(), -1, key.data(), need, nullptr, nullptr);
                if (!key.empty() && key.back() == '\0')
                    key.pop_back();
                if (!key.empty() && seen.insert(key).second)
                    out.push_back(key);
            }
        }

        if (out.empty())
            return defaultShowKeys();
        return out;
    }

    void ensureCache()
    {
        if (g_cacheLoaded)
            return;
        g_chromeShowCache = parseShowCsv(readIniString(L"chrome", L"show", L""));
        g_cacheLoaded = true;
    }
}

std::wstring StatghostPrefs::iniPath()
{
    const std::wstring dir = queryNppConfigDir();
    if (dir.empty())
        return L"";
    std::wstring path = dir;
    if (!path.empty() && path.back() != L'\\')
        path += L"\\";
    path += L"STATghost.ini";
    return path;
}

std::vector<std::string> StatghostPrefs::getChromeShow()
{
    ensureCache();
    return g_chromeShowCache;
}

void StatghostPrefs::setChromeShow(const std::vector<std::string> &keys)
{
    std::wstring csv;
    for (const std::string &key : keys)
    {
        if (key.empty())
            continue;
        if (!csv.empty())
            csv += L",";
        const int need = ::MultiByteToWideChar(CP_UTF8, 0, key.c_str(), -1, nullptr, 0);
        if (need > 0)
        {
            std::wstring wkey(static_cast<std::size_t>(need), L'\0');
            ::MultiByteToWideChar(CP_UTF8, 0, key.c_str(), -1, wkey.data(), need);
            if (!wkey.empty() && wkey.back() == L'\0')
                wkey.pop_back();
            csv += wkey;
        }
    }
    writeIniString(L"chrome", L"show", csv.c_str());
    g_chromeShowCache = keys.empty() ? defaultShowKeys() : keys;
    g_cacheLoaded = true;
}

std::wstring StatghostPrefs::getHostExe()
{
    return readIniString(L"host", L"exe", L"");
}

void StatghostPrefs::setHostExe(const std::wstring &path)
{
    writeIniString(L"host", L"exe", path.c_str());
}

bool StatghostPrefs::isChromeKeyVisible(const char *key)
{
    if (key == nullptr)
        return false;
    ensureCache();
    for (const std::string &item : g_chromeShowCache)
    {
        if (item == key)
            return true;
    }
    return false;
}

void StatghostPrefs::reloadCache()
{
    g_cacheLoaded = false;
    ensureCache();
}
