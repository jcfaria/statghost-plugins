#include "StatghostStatement.h"

#include <iostream>
#include <string>
#include <vector>

int main()
{
    const std::vector<std::string> rows = {
        "x <- runif(n,",
        "           0,",
        "           10)",
        "y <- 42",
    };

    const auto getLine = [&](int i) { return rows[static_cast<std::size_t>(i)]; };
    const int n = static_cast<int>(rows.size());

    auto [s, e] = StatghostStatement::extendStatement(0, getLine, n);
    const std::string text = StatghostStatement::dedentBlock(StatghostStatement::joinLines(getLine, s, e));
    const auto stmt = StatghostStatement::statementAtCaret(0, getLine, n);

    std::cout << "extend: " << s << " " << e << "\n";
    std::cout << text << "\n---\n";
    std::cout << "statementAtCaret end=" << stmt.end << " ok=" << stmt.ok << "\n";

    const bool ok = s == 0 && e == 2 && text.find("runif") != std::string::npos &&
                    text.find("10)") != std::string::npos && text.find("y <- 42") == std::string::npos &&
                    stmt.ok && stmt.end == 2;
    if (!ok)
        return 1;

    // Scintilla SCI_GETLINE includes trailing CRLF; joinLines must not double newlines.
    const auto getLineCrlf = [&](int i) {
        std::string line = rows[static_cast<std::size_t>(i)];
        line += "\r\n";
        return line;
    };
    const std::string joined = StatghostStatement::joinLines(getLineCrlf, 0, 2);
    if (joined.find("\n\n") != std::string::npos)
        return 2;

    return 0;
}
