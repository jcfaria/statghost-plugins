#pragma once

#include <string>

namespace StatghostProtocol
{
    constexpr wchar_t PREFIX[] = L"#. STATGHOST:";

    std::wstring makeCommand(const wchar_t *name);
    std::wstring makeEval(const std::wstring &code, bool keepFocus = true);
    std::wstring nextArmCmd(bool pluginShowsArmed);
}
