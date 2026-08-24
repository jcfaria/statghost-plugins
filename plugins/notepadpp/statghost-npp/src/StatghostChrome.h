#pragma once

#include <cstddef>
#include <string>
#include <vector>

// Keep in sync with plugins/cudatext/cuda_statghost/chrome_show.py + chrome.py icons.
namespace StatghostChrome
{
    constexpr int GRID_COLS = 3;
    constexpr std::size_t SHOW_COUNT = 26;

    const char *showKey(std::size_t index);
    const char *menuCaption(const char *key);
    const char *gridCaption(const char *key);
    const char *hintText(const char *key);
    const char *iconFile(const char *key);
    const char *methodName(const char *key);

    std::wstring menuPath(const char *key);

    enum class GridRowKind
    {
        Header,
        Cells
    };

    struct GridRow
    {
        GridRowKind kind = GridRowKind::Header;
        std::wstring title;
        std::vector<const char *> keys;
    };

    std::vector<GridRow> gridPlan();
}
