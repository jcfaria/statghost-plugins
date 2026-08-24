#pragma once

#include <string>
#include <vector>

namespace StatghostHost
{
    bool isRunning();
    std::wstring findExe();
    bool start(std::wstring &message);
    bool stopGraceful(std::wstring &message);
}
