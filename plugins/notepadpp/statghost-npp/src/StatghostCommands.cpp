#include "StatghostCommands.h"
#include "StatghostBridge.h"
#include "StatghostChrome.h"
#include "StatghostConfigDlg.h"
#include "StatghostHost.h"
#include "StatghostProtocol.h"
#include "StatghostStatement.h"
#include "PluginInterface.h"

#include <cstring>
#include <string>

namespace
{
    bool g_armed = false;

    std::wstring rQuote(const std::wstring &path)
    {
        std::wstring s = path;
        for (std::size_t pos = 0; (pos = s.find(L'\\', pos)) != std::wstring::npos; pos += 2)
            s.replace(pos, 1, L"/");
        std::wstring out = L"\"";
        for (const wchar_t ch : s)
        {
            if (ch == L'"')
                out += L"\\\"";
            else
                out += ch;
        }
        out += L"\"";
        return out;
    }

    std::wstring linesFromStart(const int lineIndex)
    {
        if (lineIndex < 0)
            return L"";
        return StatghostBridge::joinLinesWide(0, lineIndex);
    }

    std::wstring linesToEnd(const int lineIndex)
    {
        const int total = StatghostBridge::lineCount();
        if (lineIndex < 0 || lineIndex >= total)
            return L"";
        return StatghostBridge::joinLinesWide(lineIndex, total - 1);
    }

    int caretLineIndex()
    {
        const HWND sci = StatghostBridge::currentScintilla();
        if (sci == nullptr)
            return -1;
        const Sci_Position pos = static_cast<Sci_Position>(::SendMessage(sci, SCI_GETCURRENTPOS, 0, 0));
        return static_cast<int>(::SendMessage(sci, SCI_LINEFROMPOSITION, pos, 0));
    }

    void stubAction(const char *key)
    {
        const std::wstring cap(StatghostChrome::menuCaption(key),
                               StatghostChrome::menuCaption(key) + strlen(StatghostChrome::menuCaption(key)));
        StatghostBridge::setStatusMessage(L"STATghost: " + cap + L" — VP-NPP stub");
    }
}

bool StatghostCommands::isArmed()
{
    return g_armed;
}

void StatghostCommands::setArmed(const bool armed)
{
    g_armed = armed;
}

void StatghostCommands::invokeByShowIndex(const std::size_t index)
{
    invoke(StatghostChrome::showKey(index));
}

void StatghostCommands::invoke(const char *key)
{
    if (key == nullptr)
        return;

    const std::string method = StatghostChrome::methodName(key);
    if (method == "config")
    {
        const HWND parent = StatghostBridge::nppHandle();
        if (StatghostConfigDlg::showModal(parent))
            StatghostBridge::setStatusMessage(L"STATghost: Config saved");
        else
            StatghostBridge::setStatusMessage(L"STATghost: Config cancelled");
        return;
    }
    if (method == "toggle_arm")
    {
        const std::wstring payload = StatghostProtocol::nextArmCmd(g_armed);
        if (StatghostBridge::writeClipboard(payload))
        {
            g_armed = !g_armed;
            StatghostBridge::setStatusMessage(g_armed ? L"STATghost: Arm" : L"STATghost: Idle");
        }
        else
        {
            StatghostBridge::setStatusMessage(L"STATghost: clipboard failed (Arm/Idle)");
        }
        return;
    }
    if (method == "toggle_host")
    {
        std::wstring msg;
        if (StatghostHost::isRunning())
        {
            if (StatghostHost::stopGraceful(msg))
                StatghostBridge::setStatusMessage(L"STATghost: " + msg);
            else
                StatghostBridge::setStatusMessage(L"STATghost: could not quit");
        }
        else
        {
            if (StatghostHost::start(msg))
            {
                if (msg == L"already running")
                    StatghostBridge::setStatusMessage(L"STATghost: already running — one instance");
                else
                    StatghostBridge::setStatusMessage(L"STATghost: started " + msg);
            }
            else
            {
                StatghostBridge::setStatusMessage(L"STATghost: " + msg);
            }
        }
        return;
    }
    if (method == "send_selection")
    {
        std::wstring text = StatghostBridge::selectionText();
        int advanceFrom = -1;
        std::wstring mode = L"selection";
        if (text.empty() || text.find_first_not_of(L" \t\r\n") == std::wstring::npos)
        {
            const int y = caretLineIndex();
            if (y < 0)
                return;
            const int n = StatghostBridge::lineCount();
            const auto getLine = [](int i) { return StatghostBridge::lineTextUtf8(i); };
            const StatghostStatement::StatementResult stmt =
                StatghostStatement::statementAtCaret(y, getLine, n);
            if (!stmt.ok)
            {
                StatghostBridge::setStatusMessage(L"STATghost: nothing to send (selection)");
                return;
            }
            text = StatghostBridge::utf8ToWide(stmt.text);
            advanceFrom = stmt.end;
            mode = StatghostBridge::utf8ToWide(stmt.mode);
        }
        else
        {
            advanceFrom = StatghostBridge::selectionLastLine();
        }
        if (StatghostBridge::sendCode(text, mode) && advanceFrom >= 0)
            StatghostBridge::advanceCaretAfter(advanceFrom);
        return;
    }
    if (method == "send_function")
    {
        const int y = caretLineIndex();
        if (y < 0)
        {
            StatghostBridge::setStatusMessage(L"STATghost: nothing to send (function)");
            return;
        }
        const int n = StatghostBridge::lineCount();
        const auto getLine = [](int i) { return StatghostBridge::lineTextUtf8(i); };
        const auto [fs, fe] = StatghostStatement::enclosingFunction(y, getLine, n);
        if (fs < 0 || fe < 0)
        {
            StatghostBridge::setStatusMessage(L"STATghost: caret not inside a function");
            return;
        }
        const std::wstring fnText = StatghostBridge::utf8ToWide(
            StatghostStatement::dedentBlock(StatghostStatement::joinLines(getLine, fs, fe)));
        if (StatghostBridge::sendCode(fnText, L"function") && fe >= 0)
            StatghostBridge::advanceCaretAfter(fe);
        return;
    }
    if (method == "send_above")
    {
        const int y = caretLineIndex();
        if (y >= 0 && StatghostBridge::sendCode(linesFromStart(y), L"above"))
            StatghostBridge::advanceCaretAfter(y);
        return;
    }
    if (method == "send_below")
    {
        const int y = caretLineIndex();
        if (y >= 0)
            StatghostBridge::sendEval(linesToEnd(y), L"below");
        return;
    }
    if (method == "send_chunk")
    {
        stubAction(key);
        return;
    }
    if (method == "send_file" || method == "source_selection")
    {
        stubAction(key);
        return;
    }
    if (method == "set_wd_here")
    {
        const std::wstring path = StatghostBridge::currentDocumentPath();
        if (path.empty())
        {
            StatghostBridge::setStatusMessage(L"STATghost: save the file first (setwd)");
            return;
        }
        std::wstring folder = path;
        const std::size_t slash = folder.find_last_of(L"\\/");
        if (slash != std::wstring::npos)
            folder = folder.substr(0, slash);
        StatghostBridge::sendEval(L"setwd(" + rQuote(folder) + L")", L"setwd");
        return;
    }
    if (method == "inspect_print")
    {
        const std::wstring id = StatghostBridge::wordAtCaret();
        if (id.empty())
        {
            StatghostBridge::setStatusMessage(L"STATghost: no identifier to print");
            return;
        }
        StatghostBridge::sendEval(id, L"print");
        return;
    }
    if (method == "inspect_ls")
    {
        StatghostBridge::sendEval(L"ls()", L"ls");
        return;
    }
    if (method == "inspect_str")
    {
        const std::wstring id = StatghostBridge::wordAtCaret();
        StatghostBridge::sendEval(id.empty() ? L"str()" : L"str(" + id + L")", L"str");
        return;
    }
    if (method == "inspect_names")
    {
        const std::wstring id = StatghostBridge::wordAtCaret();
        StatghostBridge::sendEval(id.empty() ? L"names()" : L"names(" + id + L")", L"names");
        return;
    }
    if (method == "inspect_plot")
    {
        const std::wstring id = StatghostBridge::wordAtCaret();
        StatghostBridge::sendEval(id.empty() ? L"plot()" : L"plot(" + id + L")", L"plot");
        return;
    }
    if (method == "inspect_help")
    {
        const std::wstring id = StatghostBridge::wordAtCaret();
        if (id.empty())
        {
            StatghostBridge::setStatusMessage(L"STATghost: no identifier for help()");
            return;
        }
        StatghostBridge::sendEval(L"help(" + id + L")", L"help");
        return;
    }
    if (method == "inspect_head")
    {
        const std::wstring id = StatghostBridge::wordAtCaret();
        StatghostBridge::sendEval(id.empty() ? L"head()" : L"head(" + id + L")", L"head");
        return;
    }
    if (method == "inspect_tail")
    {
        const std::wstring id = StatghostBridge::wordAtCaret();
        StatghostBridge::sendEval(id.empty() ? L"tail()" : L"tail(" + id + L")", L"tail");
        return;
    }
    if (method == "clear_console")
    {
        StatghostBridge::sendCommand(L"CLEAR", L"Clear Console");
        return;
    }
    if (method == "inspect_graphics_off")
    {
        StatghostBridge::sendEval(L"graphics.off()", L"graphics.off");
        return;
    }
    if (method == "inspect_rm_all")
    {
        StatghostBridge::sendEval(L"rm(list=ls())", L"rm all");
        return;
    }
    if (method == "inspect_clear_all")
    {
        StatghostBridge::sendCommand(L"CLEAR", L"Clear Console");
        StatghostBridge::sendEval(L"rm(list=ls()); graphics.off()", L"clear all");
        return;
    }
    if (method == "insert_assign")
    {
        if (StatghostBridge::insertAtCaret(L" <- "))
            StatghostBridge::setStatusMessage(L"STATghost: inserted <-");
        else
            StatghostBridge::setStatusMessage(L"STATghost: no caret");
        return;
    }
    if (method == "insert_pipe")
    {
        if (StatghostBridge::insertAtCaret(L" |> "))
            StatghostBridge::setStatusMessage(L"STATghost: inserted |>");
        else
            StatghostBridge::setStatusMessage(L"STATghost: no caret");
        return;
    }
    if (method == "show_outline")
    {
        stubAction(key);
        return;
    }

    stubAction(key);
}
