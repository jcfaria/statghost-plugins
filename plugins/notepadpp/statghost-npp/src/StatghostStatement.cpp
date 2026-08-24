#include "StatghostStatement.h"

#include <algorithm>
#include <cctype>
#include <functional>
#include <limits>
#include <optional>
#include <regex>
#include <vector>

namespace StatghostStatement
{
    std::string cleanLine(const std::string &text);

    const std::regex END_OP(R"((\(|,|\+|!|\$|\^|&|\*|-|=|:|~|\||\/|\?|<|>|%[^%]*%)$)");
    const std::regex RE_R_FUN_HEAD(R"(^\s*(?:[.`\w]+|`[^`]+`)\s*(?:<-|=)\s*function\s*\()");
    const std::regex RE_PY_DEF(R"(^(\s*)(?:async\s+)?(?:def|class)\s+[A-Za-z_]\w*\s*[(:])");
    const std::regex RE_JL_FUN(R"(^\s*(?:function|macro)\s+[A-Za-z_!][\w!]*)");
    const std::regex RE_PY_OWNER(R"(^(?:async\s+)?(?:def|class|if|for|while|try|with|match)\b)");
    const std::regex RE_PY_CONTINUER(R"(^(?:elif|else|except|finally|case)\b)");
    const std::regex RE_ELSE_IF(R"(^else\s+if\b)", std::regex_constants::icase);
    const std::regex RE_ELSE_REPEAT(R"(^(else|repeat)\b)", std::regex_constants::icase);
    const std::regex RE_ELSE_REPEAT_BODY(R"(^(?:else|repeat)\b(.*)$)", std::regex_constants::icase);
    const std::regex RE_CTRL_HEAD(R"(^(?:else\s+)?(?:if|for|while)\b\s*)", std::regex_constants::icase);
    const std::regex RE_ELSE_HEAD(R"(^else\b)", std::regex_constants::icase);
    const std::regex RE_CTRL_OWNER(R"(^(?:else\s+)?(?:if|for|while|repeat)\b)", std::regex_constants::icase);
    const std::regex RE_JL_OPEN(R"(^(?:function|macro|struct|mutable\s+struct|for|while|if|let|quote|begin)\b)", std::regex_constants::icase);
    const std::regex RE_JL_END(R"(^end\b)", std::regex_constants::icase);

    enum class PySuiteKind { None, Owner, Cont, Deco };

    std::string stripTrailingLineEnd(const std::string &s)
    {
        std::size_t end = s.size();
        while (end > 0 && (s[end - 1] == '\r' || s[end - 1] == '\n'))
            --end;
        return s.substr(0, end);
    }

    std::string trimRight(const std::string &s)
    {
        std::size_t end = s.size();
        while (end > 0 && (s[end - 1] == ' ' || s[end - 1] == '\t' || s[end - 1] == '\r'))
            --end;
        return s.substr(0, end);
    }

    std::string trim(const std::string &s)
    {
        std::size_t start = 0;
        while (start < s.size() && (s[start] == ' ' || s[start] == '\t' || s[start] == '\r'))
            ++start;
        std::size_t end = s.size();
        while (end > start && (s[end - 1] == ' ' || s[end - 1] == '\t' || s[end - 1] == '\r'))
            --end;
        return s.substr(start, end - start);
    }

    std::string trimStart(const std::string &s)
    {
        std::size_t start = 0;
        while (start < s.size() && (s[start] == ' ' || s[start] == '\t' || s[start] == '\r'))
            ++start;
        return s.substr(start);
    }

    bool isQuoteChar(char c)
    {
        return c == '"' || c == '\'' || c == '`';
    }

    bool isOpenChar(char c)
    {
        return c == '(' || c == '[' || c == '{';
    }

    bool isCloseChar(char c)
    {
        return c == ')' || c == ']' || c == '}';
    }

    bool bracketsMatch(char a, char b)
    {
        if (a == ')' && b == '(')
            return true;
        if (a == ']' && b == '[')
            return true;
        if (a == '}' && b == '{')
            return true;
        if (a == '(' && b == ')')
            return true;
        if (a == '[' && b == ']')
            return true;
        if (a == '{' && b == '}')
            return true;
        return false;
    }

    PySuiteKind pySuiteKind(const std::string &line);

    struct Pos
    {
        int line = 0;
        int col = 0;
        Pos(int l, int c) : line(l), col(c) {}
    };

    char charAt(const std::string &s, int col)
    {
        if (col < 0 || static_cast<std::size_t>(col) >= s.size())
            return '\0';
        return s[static_cast<std::size_t>(col)];
    }

    std::string normalizeNewlines(const std::string &text)
    {
        std::string out;
        for (std::size_t i = 0; i < text.size(); ++i)
        {
            if (text[i] == '\r')
            {
                if (i + 1 < text.size() && text[i + 1] == '\n')
                    ++i;
                out += '\n';
            }
            else
                out += text[i];
        }
        return out;
    }

    int indentWidth(const std::string &line)
    {
        int n = 0;
        for (char c : line)
        {
            if (c == ' ')
                ++n;
            else if (c == '\t')
                n += 4;
            else
                break;
        }
        return n;
    }

    bool isBlankOrComment(const std::string &line)
    {
        const std::string s = trim(line);
        return s.empty() || s[0] == '#';
    }

    int minMargin(const std::vector<std::string> &lines)
    {
        int m = std::numeric_limits<int>::max();
        for (const std::string &ln : lines)
        {
            if (trim(ln).empty())
                continue;
            const std::size_t lead = ln.size() - trimStart(ln).size();
            if (static_cast<int>(lead) < m)
                m = static_cast<int>(lead);
        }
        return m == std::numeric_limits<int>::max() ? 0 : m;
    }

    bool newlineInsideString(const std::string &text)
    {
        char quote = '\0';
        char prev = '\0';
        for (char c : text)
        {
            if (isQuoteChar(c))
            {
                if (quote == '\0')
                    quote = c;
                else if (quote == c && prev != '\\')
                    quote = '\0';
            }
            if (c == '\n' && quote != '\0')
                return true;
            prev = c;
        }
        return false;
    }

    bool hasCodeComment(const std::string &text)
    {
        const std::string cleaned = cleanLine(text);
        return cleaned.size() < trimRight(text).size();
    }

    int callDepth(const std::string &text)
    {
        int depth = 0;
        char quote = '\0';
        char prev = '\0';
        for (char c : text)
        {
            if (quote != '\0')
            {
                if (c == quote && prev != '\\')
                    quote = '\0';
            }
            else if (isQuoteChar(c))
                quote = c;
            else if (c == '(' || c == '[')
                ++depth;
            else if (c == ')' || c == ']')
                --depth;
            prev = c;
        }
        return depth;
    }

    bool isCallContinuer(const std::string &text)
    {
        const std::string s = trimStart(text);
        if (s.empty())
            return false;
        return s[0] == ')' || s[0] == ']' || s[0] == ',';
    }

    PySuiteKind pySuiteKind(const std::string &line)
    {
        const std::string s = trim(cleanLine(line));
        if (s.empty())
            return PySuiteKind::None;
        if (s.size() >= 1 && s[0] == '@' && s.rfind("@\"", 0) != 0 && s.rfind("@'", 0) != 0)
            return PySuiteKind::Deco;
        if (s.back() != ':')
            return PySuiteKind::None;
        if (std::regex_search(s, RE_PY_OWNER))
            return PySuiteKind::Owner;
        if (std::regex_search(s, RE_PY_CONTINUER))
            return PySuiteKind::Cont;
        return PySuiteKind::None;
    }

    std::tuple<char, Pos, bool, bool> nextChar(
        Pos p,
        bool lookingForward,
        const GetLineFn &getLine,
        const std::function<bool(int)> &endsOp,
        int lineCount)
    {
        const std::string s = getLine(p.line);
        bool isEof = false;
        bool isEol = false;
        Pos nxt(p.line, p.col);
        if (lookingForward)
        {
            if (p.col != static_cast<int>(s.size()))
                nxt = Pos(p.line, p.col + 1);
            else if (p.line < lineCount - 1)
                nxt = Pos(p.line + 1, -1);
            else
            {
                isEof = true;
                nxt = Pos(p.line, p.col);
            }
            const std::string ns = getLine(nxt.line);
            if (nxt.col == static_cast<int>(ns.size()))
            {
                if (nxt.line == lineCount - 1 || !endsOp(nxt.line))
                    isEol = true;
            }
        }
        else if (p.col != -1)
            nxt = Pos(p.line, p.col - 1);
        else if (p.line > 0)
            nxt = Pos(p.line - 1, static_cast<int>(getLine(p.line - 1).size()) - 1);
        else
        {
            isEof = true;
            nxt = Pos(p.line, p.col);
        }
        if (!lookingForward && nxt.col == -1)
        {
            if (nxt.line <= 0 || !endsOp(nxt.line - 1))
                isEol = true;
        }
        const char ch = charAt(getLine(nxt.line), nxt.col);
        return {ch, nxt, isEol, isEof};
    }

    std::optional<std::string> remainderAfterControlHeader(const std::string &s)
    {
        const std::string t = trim(s);
        if (t.empty())
            return std::nullopt;
        if (std::regex_search(t, RE_ELSE_IF))
        {
            // fall through
        }
        else if (std::regex_search(t, RE_ELSE_REPEAT))
        {
            std::smatch m;
            if (std::regex_search(t, m, RE_ELSE_REPEAT_BODY))
                return trim(m[1].str());
            return std::string();
        }
        std::smatch m;
        if (!std::regex_search(t, m, RE_CTRL_HEAD))
            return std::nullopt;
        const std::string rest = t.substr(m.length());
        if (rest.empty() || rest[0] != '(')
            return std::nullopt;
        int depth = 0;
        char quote = '\0';
        char prev = '\0';
        for (std::size_t i = 0; i < rest.size(); ++i)
        {
            const char c = rest[i];
            if (quote != '\0')
            {
                if (c == quote && prev != '\\')
                    quote = '\0';
            }
            else if (isQuoteChar(c))
                quote = c;
            else if (c == '(')
                ++depth;
            else if (c == ')')
            {
                --depth;
                if (depth == 0)
                    return trim(rest.substr(i + 1));
            }
            prev = c;
        }
        return std::nullopt;
    }

    std::string joinedCode(const GetLineFn &getLine, int start, int end)
    {
        std::vector<std::string> parts;
        for (int i = start; i <= end; ++i)
            parts.push_back(cleanLine(getLine(i)));
        std::string out;
        for (std::size_t i = 0; i < parts.size(); ++i)
        {
            if (i > 0)
                out += ' ';
            out += parts[i];
        }
        return trim(out);
    }

    bool controlNeedsBody(const GetLineFn &getLine, int start, int end)
    {
        const std::optional<std::string> rem = remainderAfterControlHeader(joinedCode(getLine, start, end));
        return rem.has_value() && rem->empty();
    }

    int nextCodeLine(int i, const GetLineFn &getLine, int lineCount)
    {
        int j = i + 1;
        while (j < lineCount)
        {
            const std::string s = trim(getLine(j));
            if (s.empty())
                return -1;
            if (s[0] == '#')
            {
                ++j;
                continue;
            }
            return j;
        }
        return -1;
    }

    std::pair<int, int> extendBrackets(int line, const GetLineFn &getLine, int lineCount);

    std::pair<int, int> growRControl(
        int start,
        int end,
        const GetLineFn &getLine,
        int lineCount,
        int depth = 0)
    {
        if (depth > 32)
            return {start, end};
        bool grown = true;
        int e = end;
        while (grown)
        {
            grown = false;
            if (controlNeedsBody(getLine, start, e))
            {
                const int nxt = nextCodeLine(e, getLine, lineCount);
                if (nxt >= 0)
                {
                    auto [b0, b1] = extendBrackets(nxt, getLine, lineCount);
                    (void)b0;
                    std::tie(b0, b1) = growRControl(nxt, b1, getLine, lineCount, depth + 1);
                    if (b1 > e)
                    {
                        e = b1;
                        grown = true;
                        continue;
                    }
                }
            }
            const int nxt = nextCodeLine(e, getLine, lineCount);
            if (nxt < 0)
                break;
            const std::string head = trim(cleanLine(getLine(nxt)));
            if (std::regex_search(head, RE_ELSE_HEAD))
            {
                const std::string head0 = trim(cleanLine(getLine(start)));
                if (!std::regex_search(head0, RE_CTRL_OWNER))
                    break;
                auto [e0, e1] = extendBrackets(nxt, getLine, lineCount);
                (void)e0;
                std::tie(e0, e1) = growRControl(nxt, e1, getLine, lineCount, depth + 1);
                if (e1 > e)
                {
                    e = e1;
                    grown = true;
                }
            }
        }
        return {start, e};
    }

    int openerIfInsideString(int line, const GetLineFn &getLine)
    {
        int start = line;
        while (start > 0)
        {
            const std::string s = trim(getLine(start - 1));
            if (s.empty() || s[0] == '#')
                break;
            --start;
        }
        char quote = '\0';
        int opener = -1;
        for (int i = start; i < line; ++i)
        {
            char prev = '\0';
            for (char c : getLine(i))
            {
                if (quote != '\0')
                {
                    if (c == quote && prev != '\\')
                    {
                        quote = '\0';
                        opener = -1;
                    }
                }
                else if (isQuoteChar(c))
                {
                    quote = c;
                    opener = i;
                }
                prev = c;
            }
        }
        if (quote != '\0' && opener >= 0)
            return opener;
        return line;
    }

    int includeDecorators(int start, const GetLineFn &getLine)
    {
        int i = start;
        while (i > 0)
        {
            if (pySuiteKind(getLine(i - 1)) == PySuiteKind::Deco)
            {
                --i;
                continue;
            }
            break;
        }
        return i;
    }

    int pyFindOwner(int line, const GetLineFn &getLine)
    {
        const int myInd = indentWidth(getLine(line));
        for (int j = line - 1; j >= 0; --j)
        {
            const std::string raw = getLine(j);
            const std::string s = trim(raw);
            if (s.empty())
                return -1;
            if (s[0] == '#')
                continue;
            const int ind = indentWidth(raw);
            if (ind > myInd)
                continue;
            if (ind < myInd)
                return -1;
            const PySuiteKind kind = pySuiteKind(raw);
            if (kind == PySuiteKind::Owner)
                return j;
            if (kind == PySuiteKind::Cont)
                continue;
            return -1;
        }
        return -1;
    }

    int pyExtendSuite(int start, const GetLineFn &getLine, int lineCount)
    {
        int i = start;
        while (i < lineCount && pySuiteKind(getLine(i)) == PySuiteKind::Deco)
            ++i;
        if (i >= lineCount)
            return start;
        const PySuiteKind kind = pySuiteKind(getLine(i));
        if (kind != PySuiteKind::Owner && kind != PySuiteKind::Cont)
            return i > start ? i - 1 : start;
        const int headInd = indentWidth(getLine(i));
        int end = i;
        int j = i + 1;
        while (j < lineCount)
        {
            const std::string raw = getLine(j);
            const std::string s = trim(raw);
            if (s.empty())
                return end;
            if (s[0] == '#')
            {
                ++j;
                continue;
            }
            const int ind = indentWidth(raw);
            const PySuiteKind nxt = pySuiteKind(raw);
            if (ind > headInd)
            {
                end = j;
                ++j;
                continue;
            }
            if (ind == headInd && nxt == PySuiteKind::Cont)
            {
                end = j;
                ++j;
                continue;
            }
            break;
        }
        return end;
    }

    std::pair<int, int> growPyCompound(int start, int end, const GetLineFn &getLine, int lineCount)
    {
        const PySuiteKind kind = pySuiteKind(getLine(start));
        if (kind == PySuiteKind::None)
            return {start, end};
        int i = start;
        if (kind == PySuiteKind::Cont)
        {
            const int owner = pyFindOwner(i, getLine);
            if (owner >= 0)
                i = owner;
        }
        i = includeDecorators(i, getLine);
        int newEnd = pyExtendSuite(i, getLine, lineCount);
        if (newEnd < end)
            newEnd = end;
        return {i, newEnd};
    }

    std::pair<int, int> extendBrackets(int line, const GetLineFn &getLine, int lineCount)
    {
        if (lineCount <= 0)
            return {0, 0};
        int ln = line;
        if (ln < 0)
            ln = 0;
        if (ln >= lineCount)
            ln = lineCount - 1;

        const auto lineAt = [&](int i) { return getLine(i); };
        const auto endsOp = [&](int i) { return endsInOperator(lineAt(i)); };

        bool lookingForward = true;
        std::vector<Pos> poss = {Pos(ln, 0), Pos(ln, -1)};
        bool done[2] = {false, false};
        std::vector<std::vector<char>> unmatched = {{}, {}};
        bool abort = false;
        char quote = '\0';
        char prev = '\0';

        while (!abort && !(done[0] && done[1]))
        {
            const int d = lookingForward ? 1 : 0;
            auto [ch, nxt, isEol, isEof] = nextChar(poss[d], lookingForward, lineAt, endsOp, lineCount);
            poss[d] = nxt;
            if (quote == '\0')
            {
                if (isQuoteChar(ch))
                    quote = ch;
                else if (lookingForward ? isOpenChar(ch) : isCloseChar(ch))
                    unmatched[d].push_back(ch);
                else if (lookingForward ? isCloseChar(ch) : isOpenChar(ch))
                {
                    if (unmatched[d].empty())
                    {
                        lookingForward = !lookingForward;
                        const int d2 = lookingForward ? 1 : 0;
                        unmatched[d2].push_back(ch);
                        done[d2] = false;
                    }
                    else
                    {
                        const char open = unmatched[d].back();
                        unmatched[d].pop_back();
                        if (!bracketsMatch(ch, open))
                            abort = true;
                    }
                }
            }
            else if (ch == quote)
            {
                if (lookingForward)
                {
                    if (prev != '\\')
                        quote = '\0';
                }
                else
                {
                    auto [nch, _, __, ___] = nextChar(poss[d], lookingForward, lineAt, endsOp, lineCount);
                    (void)_;
                    (void)__;
                    (void)___;
                    if (nch != '\\')
                        quote = '\0';
                }
            }
            if (isEol)
            {
                if (quote != '\0')
                {
                    if (isEof)
                        abort = true;
                }
                else if (unmatched[lookingForward ? 1 : 0].empty())
                {
                    done[lookingForward ? 1 : 0] = true;
                    lookingForward = !lookingForward;
                }
                else if (isEof)
                    abort = true;
            }
            prev = ch;
        }
        if (abort)
            return {ln, ln};
        return {poss[0].line, poss[1].line};
    }
std::string cleanLine(const std::string &text)
{
    if (text.empty())
        return "";
    std::string out;
    char quote = '\0';
    char prev = '\0';
    for (char c : text)
    {
        if (c == '"' || c == '\'' || c == '`')
        {
            if (quote == '\0')
                quote = c;
            else if (quote == c && prev != '\\')
                quote = '\0';
        }
        if (c == '#' && quote == '\0')
            break;
        out += c;
        prev = c;
    }
    return trimRight(out);
}

bool endsInOperator(const std::string &text)
{
    const std::string raw = trim(text);
    if (raw.empty() || raw[0] == '#')
        return false;
    const std::string s = cleanLine(text);
    if (trim(s).empty())
        return false;
    const PySuiteKind kind = pySuiteKind(text);
    if (kind == PySuiteKind::Owner || kind == PySuiteKind::Cont)
        return false;
    return std::regex_search(s, END_OP);
}

std::string collapseWraps(const std::string &text)
{
    if (text.empty() || text.find('\n') == std::string::npos)
        return text;
    const std::string raw = normalizeNewlines(text);
    if (newlineInsideString(raw))
        return text;
    std::vector<std::string> lines;
    std::size_t start = 0;
    for (std::size_t i = 0; i <= raw.size(); ++i)
    {
        if (i == raw.size() || raw[i] == '\n')
        {
            lines.push_back(raw.substr(start, i - start));
            start = i + 1;
        }
    }
    if (lines.empty())
        return text;
    std::vector<std::string> out;
    out.push_back(trimRight(lines[0]));
    for (std::size_t li = 1; li < lines.size(); ++li)
    {
        const std::string &line = lines[li];
        const std::string &prev = out.back();
        const std::string nxt = trim(line);
        if (nxt.empty() || nxt[0] == '#')
        {
            out.push_back(line);
            continue;
        }
        bool join = false;
        if (!prev.empty() && !hasCodeComment(prev))
        {
            if (endsInOperator(prev))
                join = true;
            else if (callDepth(prev) > 0 && isCallContinuer(nxt))
                join = true;
        }
        if (join)
            out.back() = prev + " " + nxt;
        else
            out.push_back(trimRight(line));
    }
    std::string result;
    for (std::size_t i = 0; i < out.size(); ++i)
    {
        if (i > 0)
            result += '\n';
        result += out[i];
    }
    return result;
}

std::string dedentBlock(const std::string &text)
{
    if (text.empty())
        return text;
    const std::string raw = normalizeNewlines(text);
    if (trim(raw).empty())
        return raw;
    std::vector<std::string> lines;
    std::size_t start = 0;
    for (std::size_t i = 0; i <= raw.size(); ++i)
    {
        if (i == raw.size() || raw[i] == '\n')
        {
            lines.push_back(raw.substr(start, i - start));
            start = i + 1;
        }
    }
    const int margin = minMargin(lines);
    if (margin <= 0)
        return raw;
    std::string out;
    for (std::size_t i = 0; i < lines.size(); ++i)
    {
        if (i > 0)
            out += '\n';
        const std::string &ln = lines[i];
        if (trim(ln).empty())
            out += ln;
        else
            out += ln.substr(static_cast<std::size_t>(margin));
    }
    return out;
}

std::pair<int, int> extendStatement(int line, const GetLineFn &getLine, int lineCount)
{
    const int opener = openerIfInsideString(line, getLine);
    auto [start, end] = extendBrackets(opener, getLine, lineCount);
    std::tie(start, end) = growRControl(start, end, getLine, lineCount);
    return growPyCompound(start, end, getLine, lineCount);
}

std::pair<int, int> enclosingFunction(int line, const GetLineFn &getLine, int lineCount)
{
    if (lineCount <= 0)
        return {-1, -1};
    int ln = line;
    if (ln < 0)
        ln = 0;
    if (ln >= lineCount)
        ln = lineCount - 1;

    const auto lineAt = [&](int i) { return getLine(i); };

    for (int i = ln; i >= 0; --i)
    {
        const std::string raw = lineAt(i);
        if (!std::regex_search(raw, RE_R_FUN_HEAD))
            continue;
        auto [s, e] = extendStatement(i, getLine, lineCount);
        if (s <= ln && ln <= e)
            return {s, e};
    }

    const std::string caretRaw = lineAt(ln);
    int caretInd = indentWidth(caretRaw);
    int searchFrom = ln;
    if (pySuiteKind(caretRaw) == PySuiteKind::Deco)
    {
        int j = ln + 1;
        while (j < lineCount && (pySuiteKind(lineAt(j)) == PySuiteKind::Deco || isBlankOrComment(lineAt(j))))
            ++j;
        if (j < lineCount && std::regex_search(lineAt(j), RE_PY_DEF))
        {
            searchFrom = j;
            caretInd = indentWidth(lineAt(j));
        }
    }
    if (isBlankOrComment(caretRaw) && pySuiteKind(caretRaw) != PySuiteKind::Deco)
    {
        bool found = false;
        for (int j = ln + 1; j < lineCount; ++j)
        {
            if (!isBlankOrComment(lineAt(j)))
            {
                caretInd = indentWidth(lineAt(j));
                found = true;
                break;
            }
        }
        if (!found)
        {
            for (int j = ln - 1; j >= 0; --j)
            {
                if (!isBlankOrComment(lineAt(j)))
                {
                    caretInd = indentWidth(lineAt(j));
                    break;
                }
            }
        }
    }
    for (int i = searchFrom; i >= 0; --i)
    {
        const std::string raw = lineAt(i);
        if (!std::regex_search(raw, RE_PY_DEF))
            continue;
        const int headInd = indentWidth(raw);
        if (headInd > caretInd)
            continue;
        int end = i;
        for (int j = i + 1; j < lineCount; ++j)
        {
            const std::string lj = lineAt(j);
            if (isBlankOrComment(lj))
                continue;
            if (indentWidth(lj) > headInd)
            {
                end = j;
                continue;
            }
            break;
        }
        const int deco = includeDecorators(i, lineAt);
        if (deco <= ln && ln <= end)
            return {deco, end};
    }

    for (int i = ln; i >= 0; --i)
    {
        const std::string raw = lineAt(i);
        if (!std::regex_search(raw, RE_JL_FUN))
            continue;
        int depth = 1;
        int end = i;
        for (int j = i + 1; j < lineCount; ++j)
        {
            const std::string lj = trim(lineAt(j));
            if (std::regex_search(lj, RE_JL_OPEN))
                ++depth;
            if (std::regex_search(lj, RE_JL_END))
            {
                --depth;
                if (depth == 0)
                {
                    end = j;
                    break;
                }
            }
            end = j;
        }
        if (i <= ln && ln <= end && depth == 0)
            return {i, end};
    }

    return {-1, -1};
}

std::string joinLines(const GetLineFn &getLine, int start, int end)
{
    std::string out;
    for (int i = start; i <= end; ++i)
    {
        if (i > start)
            out += '\n';
        out += stripTrailingLineEnd(getLine(i));
    }
    return out;
}

StatementResult statementAtCaret(int caretLine, const GetLineFn &getLine, int lineCount)
{
    StatementResult result;
    result.mode = "statement";
    if (caretLine < 0)
        return result;

    auto [fs, fe] = enclosingFunction(caretLine, getLine, lineCount);
    if (fs >= 0 && fe >= 0)
    {
        result.start = fs;
        result.end = fe;
        result.text = dedentBlock(joinLines(getLine, fs, fe));
        result.mode = "function";
        result.ok = !trim(result.text).empty();
        return result;
    }

    int y = caretLine;
    while (y < lineCount && isBlankOrComment(getLine(y)))
        ++y;
    if (y >= lineCount)
        return result;

    auto [start, end] = extendStatement(y, getLine, lineCount);
    result.start = start;
    result.end = end;
    result.text = dedentBlock(joinLines(getLine, start, end));
    result.ok = !trim(result.text).empty();
    return result;
}

} // namespace StatghostStatement
