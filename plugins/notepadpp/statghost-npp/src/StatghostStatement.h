#pragma once

#include <functional>
#include <string>
#include <utility>

namespace StatghostStatement
{
    using GetLineFn = std::function<std::string(int)>;

    std::string cleanLine(const std::string &text);
    bool endsInOperator(const std::string &text);
    std::string collapseWraps(const std::string &text);
    std::string dedentBlock(const std::string &text);
    std::pair<int, int> extendStatement(int line, const GetLineFn &getLine, int lineCount);
    std::pair<int, int> enclosingFunction(int line, const GetLineFn &getLine, int lineCount);
    std::string joinLines(const GetLineFn &getLine, int start, int end);

    struct StatementResult
    {
        int start = -1;
        int end = -1;
        std::string text;
        std::string mode; // "function" | "statement"
        bool ok = false;
    };

    StatementResult statementAtCaret(int caretLine, const GetLineFn &getLine, int lineCount);
}
