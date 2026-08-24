#include "StatghostBridge.h"
#include "StatghostProtocol.h"
#include "StatghostStatement.h"
#include "PluginInterface.h"

#include <shlwapi.h>

namespace
{
    NppData *g_npp = nullptr;

    std::wstring queryNppString(const UINT msg, const WPARAM wParam = 0)
    {
        if (g_npp == nullptr || g_npp->_nppHandle == nullptr)
            return L"";

        const int len = static_cast<int>(::SendMessage(g_npp->_nppHandle, msg, wParam, 0));
        if (len <= 0)
            return L"";

        std::wstring buffer(static_cast<std::size_t>(len) + 1, L'\0');
        ::SendMessage(g_npp->_nppHandle, msg, static_cast<WPARAM>(len + 1),
                      reinterpret_cast<LPARAM>(buffer.data()));
        buffer.resize(static_cast<std::size_t>(len));
        return buffer;
    }

    std::wstring utf8ToWideImpl(const char *utf8)
    {
        if (utf8 == nullptr || utf8[0] == '\0')
            return L"";
        const int need = ::MultiByteToWideChar(CP_UTF8, 0, utf8, -1, nullptr, 0);
        if (need <= 0)
            return L"";
        std::wstring out(static_cast<std::size_t>(need), L'\0');
        ::MultiByteToWideChar(CP_UTF8, 0, utf8, -1, out.data(), need);
        if (!out.empty() && out.back() == L'\0')
            out.pop_back();
        return out;
    }

    std::string wideToUtf8(const std::wstring &wide)
    {
        if (wide.empty())
            return "";
        const int need = ::WideCharToMultiByte(CP_UTF8, 0, wide.c_str(), static_cast<int>(wide.size()),
                                               nullptr, 0, nullptr, nullptr);
        if (need <= 0)
            return "";
        std::string out(static_cast<std::size_t>(need), '\0');
        ::WideCharToMultiByte(CP_UTF8, 0, wide.c_str(), static_cast<int>(wide.size()), out.data(), need,
                              nullptr, nullptr);
        return out;
    }
}

void StatghostBridge::init(NppData *data)
{
    g_npp = data;
}

HWND StatghostBridge::nppHandle()
{
    return (g_npp != nullptr) ? g_npp->_nppHandle : nullptr;
}

void StatghostBridge::setStatusMessage(const std::wstring &message)
{
    if (g_npp == nullptr || g_npp->_nppHandle == nullptr)
        return;
    ::SendMessage(g_npp->_nppHandle, NPPM_SETSTATUSBAR, STATUSBAR_TYPING_MODE,
                  reinterpret_cast<LPARAM>(message.c_str()));
}

bool StatghostBridge::writeClipboard(const std::wstring &text)
{
    if (!::OpenClipboard(nullptr))
        return false;

    ::EmptyClipboard();
    bool ok = false;

    const std::size_t bytes = (text.size() + 1) * sizeof(wchar_t);
    HGLOBAL mem = ::GlobalAlloc(GMEM_MOVEABLE, bytes);
    if (mem != nullptr)
    {
        void *dest = ::GlobalLock(mem);
        if (dest != nullptr)
        {
            memcpy(dest, text.c_str(), bytes);
            ::GlobalUnlock(mem);
            if (::SetClipboardData(CF_UNICODETEXT, mem) != nullptr)
                ok = true;
            else
                ::GlobalFree(mem);
        }
        else
        {
            ::GlobalFree(mem);
        }
    }

    ::CloseClipboard();
    return ok;
}

void StatghostBridge::sendCommand(const wchar_t *cmdName, const std::wstring &hint)
{
    const std::wstring payload = StatghostProtocol::makeCommand(cmdName);
    if (writeClipboard(payload))
        setStatusMessage(L"STATghost: " + hint);
    else
        setStatusMessage(L"STATghost: clipboard failed (" + hint + L")");
}

bool StatghostBridge::sendEval(const std::wstring &code, const std::wstring &modeHint, const bool keepFocus)
{
    if (code.empty() || code.find_first_not_of(L" \t\r\n") == std::wstring::npos)
    {
        setStatusMessage(L"STATghost: nothing to send (" + modeHint + L")");
        return false;
    }

    const std::wstring payload = StatghostProtocol::makeEval(code, keepFocus);
    if (!writeClipboard(payload))
    {
        setStatusMessage(L"STATghost: clipboard failed (" + modeHint + L")");
        return false;
    }

    const std::wstring status = L"STATghost: sent " + modeHint + L" (" +
                                std::to_wstring(code.size()) + L" chars) — Armed?";
    setStatusMessage(status);
    return true;
}

HWND StatghostBridge::currentScintilla()
{
    if (g_npp == nullptr || g_npp->_nppHandle == nullptr)
        return nullptr;

    int which = -1;
    ::SendMessage(g_npp->_nppHandle, NPPM_GETCURRENTSCINTILLA, 0, reinterpret_cast<LPARAM>(&which));
    return which == 0 ? g_npp->_scintillaMainHandle : g_npp->_scintillaSecondHandle;
}

std::wstring StatghostBridge::selectionText()
{
    const HWND sci = currentScintilla();
    if (sci == nullptr)
        return L"";

    const Sci_Position start = static_cast<Sci_Position>(::SendMessage(sci, SCI_GETSELECTIONSTART, 0, 0));
    const Sci_Position end = static_cast<Sci_Position>(::SendMessage(sci, SCI_GETSELECTIONEND, 0, 0));
    if (start == end)
        return L"";

    const Sci_Position len = end - start;
    std::string utf8(static_cast<std::size_t>(len) + 1, '\0');
    ::SendMessage(sci, SCI_GETSELTEXT, 0, reinterpret_cast<LPARAM>(utf8.data()));
    utf8.resize(static_cast<std::size_t>(len));
    return utf8ToWideImpl(utf8.c_str());
}

std::wstring StatghostBridge::lineText(const int lineIndex)
{
    const HWND sci = currentScintilla();
    if (sci == nullptr || lineIndex < 0)
        return L"";

    const Sci_Position len = static_cast<Sci_Position>(
        ::SendMessage(sci, SCI_LINELENGTH, static_cast<WPARAM>(lineIndex), 0));
    if (len <= 0)
        return L"";

    std::string utf8(static_cast<std::size_t>(len) + 1, '\0');
    ::SendMessage(sci, SCI_GETLINE, static_cast<WPARAM>(lineIndex), reinterpret_cast<LPARAM>(utf8.data()));
    utf8.resize(static_cast<std::size_t>(len));
    while (!utf8.empty() && (utf8.back() == '\r' || utf8.back() == '\n'))
        utf8.pop_back();
    return utf8ToWideImpl(utf8.c_str());
}

std::wstring StatghostBridge::utf8ToWide(const std::string &utf8)
{
    return utf8ToWideImpl(utf8.c_str());
}

int StatghostBridge::lineCount()
{
    const HWND sci = currentScintilla();
    if (sci == nullptr)
        return 0;
    return static_cast<int>(::SendMessage(sci, SCI_GETLINECOUNT, 0, 0));
}

std::string StatghostBridge::lineTextUtf8(int lineIndex)
{
    return wideToUtf8(lineText(lineIndex));
}

std::wstring StatghostBridge::joinLinesWide(int start, int end)
{
    std::wstring out;
    for (int i = start; i <= end; ++i)
    {
        if (i > start)
            out += L"\n";
        out += lineText(i);
    }
    return out;
}

bool StatghostBridge::sendCode(const std::wstring &code, const std::wstring &modeHint, const bool applyCollapse)
{
    if (code.empty() || code.find_first_not_of(L" \t\r\n") == std::wstring::npos)
    {
        setStatusMessage(L"STATghost: nothing to send (" + modeHint + L")");
        return false;
    }

    std::string utf8 = wideToUtf8(code);
    utf8 = StatghostStatement::dedentBlock(utf8);
    if (applyCollapse)
        utf8 = StatghostStatement::collapseWraps(utf8);

    return sendEval(utf8ToWide(utf8), modeHint);
}

std::wstring StatghostBridge::currentLineText()
{
    const HWND sci = currentScintilla();
    if (sci == nullptr)
        return L"";

    const Sci_Position pos = static_cast<Sci_Position>(::SendMessage(sci, SCI_GETCURRENTPOS, 0, 0));
    const int line = static_cast<int>(::SendMessage(sci, SCI_LINEFROMPOSITION, pos, 0));
    return lineText(line);
}

bool StatghostBridge::isBlankOrHashComment(const std::wstring &line)
{
    std::size_t i = 0;
    while (i < line.size() && (line[i] == L' ' || line[i] == L'\t' || line[i] == L'\r'))
        ++i;
    if (i >= line.size() || line[i] == L'\n')
        return true;
    return line[i] == L'#';
}

int StatghostBridge::selectionLastLine()
{
    const HWND sci = currentScintilla();
    if (sci == nullptr)
        return -1;

    const Sci_Position anchor = static_cast<Sci_Position>(::SendMessage(sci, SCI_GETANCHOR, 0, 0));
    const Sci_Position current = static_cast<Sci_Position>(::SendMessage(sci, SCI_GETCURRENTPOS, 0, 0));
    if (anchor == current)
        return -1;

    const Sci_Position ay = static_cast<Sci_Position>(::SendMessage(sci, SCI_LINEFROMPOSITION, anchor, 0));
    const Sci_Position cy = static_cast<Sci_Position>(::SendMessage(sci, SCI_LINEFROMPOSITION, current, 0));
    const bool forward = ay < cy || (ay == cy && anchor <= current);
    const Sci_Position endLine = forward ? cy : ay;
    const Sci_Position endPos = forward ? current : anchor;
    const Sci_Position startLine = forward ? ay : cy;
    Sci_Position last = endLine;
    const Sci_Position lineStart = static_cast<Sci_Position>(
        ::SendMessage(sci, SCI_POSITIONFROMLINE, endLine, 0));
    if (endPos == lineStart && endLine > startLine)
        last = endLine - 1;
    return static_cast<int>(last);
}

void StatghostBridge::advanceCaretAfter(const int fromLine)
{
    const HWND sci = currentScintilla();
    if (sci == nullptr || fromLine < 0)
        return;

    const int total = static_cast<int>(::SendMessage(sci, SCI_GETLINECOUNT, 0, 0));
    int y = fromLine + 1;
    while (y < total)
    {
        if (!isBlankOrHashComment(lineText(y)))
        {
            const Sci_Position pos = static_cast<Sci_Position>(
                ::SendMessage(sci, SCI_POSITIONFROMLINE, static_cast<WPARAM>(y), 0));
            ::SendMessage(sci, SCI_SETSEL, static_cast<WPARAM>(pos), static_cast<LPARAM>(pos));
            ::SendMessage(sci, SCI_VERTICALCENTRECARET, 0, 0);
            return;
        }
        ++y;
    }
}

std::wstring StatghostBridge::wordAtCaret()
{
    const HWND sci = currentScintilla();
    if (sci == nullptr)
        return L"";

    const Sci_Position pos = static_cast<Sci_Position>(::SendMessage(sci, SCI_GETCURRENTPOS, 0, 0));
    const Sci_Position start = static_cast<Sci_Position>(::SendMessage(sci, SCI_WORDSTARTPOSITION, pos, TRUE));
    const Sci_Position end = static_cast<Sci_Position>(::SendMessage(sci, SCI_WORDENDPOSITION, pos, TRUE));
    if (end <= start)
        return L"";

    Sci_TextRangeFull tr = {};
    tr.chrg.cpMin = start;
    tr.chrg.cpMax = end;
    std::string utf8(static_cast<std::size_t>(end - start) + 1, '\0');
    tr.lpstrText = utf8.data();
    ::SendMessage(sci, SCI_GETTEXTRANGEFULL, 0, reinterpret_cast<LPARAM>(&tr));
    utf8.resize(static_cast<std::size_t>(end - start));
    return utf8ToWideImpl(utf8.c_str());
}

std::wstring StatghostBridge::currentDocumentPath()
{
    if (g_npp == nullptr || g_npp->_nppHandle == nullptr)
        return L"";

    const int index = static_cast<int>(::SendMessage(g_npp->_nppHandle, NPPM_GETCURRENTDOCINDEX, 0, 0));
    if (index < 0)
        return L"";

    const UINT_PTR bufferId = static_cast<UINT_PTR>(::SendMessage(g_npp->_nppHandle, NPPM_GETBUFFERIDFROMPOS, index, 0));
    const int len = static_cast<int>(::SendMessage(g_npp->_nppHandle, NPPM_GETFULLPATHFROMBUFFERID, bufferId, 0));
    if (len <= 0)
        return L"";

    std::wstring path(static_cast<std::size_t>(len) + 1, L'\0');
    ::SendMessage(g_npp->_nppHandle, NPPM_GETFULLPATHFROMBUFFERID, bufferId,
                  reinterpret_cast<LPARAM>(path.data()));
    path.resize(static_cast<std::size_t>(len));
    return path;
}

std::wstring StatghostBridge::pluginHomeDir()
{
    const std::wstring root = queryNppString(NPPM_GETPLUGINHOMEPATH);
    if (root.empty())
        return L"";

    std::wstring home = root;
    if (home.back() != L'\\')
        home += L"\\";
    home += L"STATghost";
    return home;
}

std::wstring StatghostBridge::sharedResDir()
{
    const std::wstring home = pluginHomeDir();
    if (home.empty())
        return L"";

    std::wstring shared = home + L"\\res\\shared";
    if (::PathIsDirectoryW(shared.c_str()))
        return shared;

    return home + L"\\res";
}

bool StatghostBridge::insertAtCaret(const std::wstring &text)
{
    const HWND sci = currentScintilla();
    if (sci == nullptr || text.empty())
        return false;

    const int need = ::WideCharToMultiByte(CP_UTF8, 0, text.c_str(), static_cast<int>(text.size()),
                                           nullptr, 0, nullptr, nullptr);
    if (need <= 0)
        return false;

    std::string utf8(static_cast<std::size_t>(need), '\0');
    ::WideCharToMultiByte(CP_UTF8, 0, text.c_str(), static_cast<int>(text.size()), utf8.data(), need,
                          nullptr, nullptr);
    ::SendMessage(sci, SCI_REPLACESEL, 0, reinterpret_cast<LPARAM>(utf8.c_str()));
    return true;
}

std::wstring StatghostBridge::readClipboardText()
{
    if (!::OpenClipboard(nullptr))
        return L"";

    std::wstring out;
    HANDLE data = ::GetClipboardData(CF_UNICODETEXT);
    if (data != nullptr)
    {
        const wchar_t *raw = static_cast<const wchar_t *>(::GlobalLock(data));
        if (raw != nullptr)
        {
            out = raw;
            ::GlobalUnlock(data);
        }
    }
    ::CloseClipboard();
    return out;
}
