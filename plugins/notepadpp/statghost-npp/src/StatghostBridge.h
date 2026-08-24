#pragma once

#include "PluginInterface.h"

#include <string>

namespace StatghostBridge
{
    void init(NppData *data);
    HWND nppHandle();

    void setStatusMessage(const std::wstring &message);
    bool writeClipboard(const std::wstring &text);
    void sendCommand(const wchar_t *cmdName, const std::wstring &hint);
    bool sendEval(const std::wstring &code, const std::wstring &modeHint, bool keepFocus = true);

    HWND currentScintilla();
    std::wstring selectionText();
    std::wstring lineText(int lineIndex);
    std::wstring currentLineText();
    int selectionLastLine();
    bool isBlankOrHashComment(const std::wstring &line);
    void advanceCaretAfter(int fromLine);
    std::wstring wordAtCaret();
    std::wstring currentDocumentPath();
    std::wstring pluginHomeDir();
    std::wstring sharedResDir();
    bool insertAtCaret(const std::wstring &text);
    std::wstring readClipboardText();

    int lineCount();
    std::string lineTextUtf8(int lineIndex);
    std::wstring utf8ToWide(const std::string &utf8);
    std::wstring joinLinesWide(int start, int end);
    bool sendCode(const std::wstring &code, const std::wstring &modeHint, bool applyCollapse = true);
}
