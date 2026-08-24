#include "StatghostProtocol.h"

#include <chrono>

namespace
{
    std::wstring upperWide(const wchar_t *text)
    {
        if (text == nullptr)
            return L"";
        std::wstring out(text);
        for (wchar_t &ch : out)
        {
            if (ch >= L'a' && ch <= L'z')
                ch = static_cast<wchar_t>(ch - L'a' + L'A');
        }
        return out;
    }

    std::wstring nonce()
    {
        static int counter = 0;
        ++counter;
        const auto ns = std::chrono::steady_clock::now().time_since_epoch().count();
        return std::to_wstring(ns) + L"-" + std::to_wstring(counter);
    }
}

std::wstring StatghostProtocol::makeCommand(const wchar_t *name)
{
    const std::wstring cmd = upperWide(name);
    return std::wstring(PREFIX) + cmd + L" " + nonce();
}

std::wstring StatghostProtocol::makeEval(const std::wstring &code, const bool keepFocus)
{
    const wchar_t *cmd = keepFocus ? L"EVAL_KEEP" : L"EVAL";
    return makeCommand(cmd) + L"\n" + code;
}

std::wstring StatghostProtocol::nextArmCmd(const bool pluginShowsArmed)
{
    return makeCommand(pluginShowsArmed ? L"IDLE" : L"ARM");
}
