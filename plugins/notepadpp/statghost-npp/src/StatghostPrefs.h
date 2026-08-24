#pragma once

#include <string>
#include <vector>

namespace StatghostPrefs
{
    std::wstring iniPath();

    std::vector<std::string> getChromeShow();
    void setChromeShow(const std::vector<std::string> &keys);

    std::wstring getHostExe();
    void setHostExe(const std::wstring &path);

    bool isChromeKeyVisible(const char *key);
    void reloadCache();
}
