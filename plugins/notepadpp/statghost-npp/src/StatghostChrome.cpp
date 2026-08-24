#include "StatghostChrome.h"

#include "StatghostPrefs.h"

#include <cstring>
#include <unordered_map>

namespace
{
    constexpr const char *DEFAULT_SHOW[] = {
        "cfg", "arm", "host",
        "send", "function", "above", "below", "chunk",
        "source", "srcsel", "setwd",
        "inspect", "ls", "str", "names", "plot", "help", "head", "tail",
        "clear", "close_graphics", "remove_objects", "clear_all",
        "assign", "pipe", "outline",
    };

    struct NestEntry
    {
        const char *parent;
        const char *label;
    };

    constexpr NestEntry NEST_MENU[] = {
        {"send", "Send"},
        {"source", "Source"},
        {"inspect", "Inspect"},
        {"clear", "Clear"},
    };

    constexpr const char *NEST_CHILDREN[][8] = {
        {"function", "above", "below", "chunk", nullptr},
        {"srcsel", "setwd", nullptr},
        {"ls", "str", "names", "plot", "help", "head", "tail", nullptr},
        {"close_graphics", "remove_objects", "clear_all", nullptr},
    };

    struct GroupDef
    {
        const char *title;
        const char *keys[8];
    };

    constexpr GroupDef GRID_GROUPS[] = {
        {"Host", {"cfg", "arm", "host", nullptr}},
        {"Send", {"send", "function", "above", "below", "chunk", nullptr}},
        {"Source", {"source", "srcsel", "setwd", nullptr}},
        {"Inspect", {"inspect", "ls", "str", "names", "plot", "help", "head", "tail"}},
        {"Clear", {"clear", "close_graphics", "remove_objects", "clear_all", nullptr}},
        {"Edit", {"assign", "pipe", "outline", nullptr}},
    };

    const char *lookup(const std::unordered_map<std::string, const char *> &map, const char *key)
    {
        const auto it = map.find(key ? key : "");
        return it != map.end() ? it->second : key;
    }

    const char *MENU_CAP(const char *key)
    {
        static const std::unordered_map<std::string, const char *> map = {
            {"cfg", "Config"}, {"arm", "Toggle Arm/Idle"}, {"host", "Start/Quit STATghost"},
            {"send", "Send"}, {"function", "Function"}, {"above", "Above"}, {"below", "Below"},
            {"chunk", "Chunk"}, {"source", "Source"}, {"srcsel", "Src sel"}, {"setwd", "setwd"},
            {"inspect", "Print"}, {"ls", "ls()"}, {"str", "str()"}, {"names", "names()"},
            {"plot", "plot()"}, {"help", "Help"}, {"head", "head()"}, {"tail", "tail()"},
            {"clear", "Clear"}, {"close_graphics", "graphics.off"}, {"remove_objects", "rm all"},
            {"clear_all", "Clear all"}, {"assign", "Insert <-"}, {"pipe", "Insert pipe"},
            {"outline", "Outline…"},
        };
        return lookup(map, key);
    }

    const char *GRID_CAP(const char *key)
    {
        static const std::unordered_map<std::string, const char *> map = {
            {"cfg", "Config"}, {"arm", "Idle"}, {"host", "Start"}, {"send", "Send"},
            {"function", "Func"}, {"above", "Above"}, {"below", "Below"}, {"chunk", "Chunk"},
            {"source", "Source"}, {"srcsel", "Sel"}, {"setwd", "setwd"}, {"inspect", "Print"},
            {"ls", "ls"}, {"str", "str"}, {"names", "names"}, {"plot", "plot"}, {"help", "help"},
            {"head", "head"}, {"tail", "tail"}, {"clear", "Clear"}, {"close_graphics", "g.off"},
            {"remove_objects", "rm"}, {"clear_all", "all"}, {"assign", "<-"}, {"pipe", "pipe"},
            {"outline", "out"},
        };
        return lookup(map, key);
    }

    const char *HINT_TEXT(const char *key)
    {
        static const std::unordered_map<std::string, const char *> map = {
            {"cfg", "STATghost plugin Config"}, {"arm", "Toggle Arm/Idle"},
            {"host", "Start/Quit STATghost"},
            {"send", "Send selection, enclosing function, or statement"},
            {"function", "Send enclosing function"}, {"above", "Send above (start→caret)"},
            {"below", "Send below (caret→EOF)"}, {"chunk", "Send sniper chunk"},
            {"source", "Source file via .paths[4]"},
            {"srcsel", "Source selection / function via .paths[5]"},
            {"setwd", "setwd to file directory"}, {"inspect", "Print identifier under caret"},
            {"ls", "ls()"}, {"str", "str() of identifier under caret"},
            {"names", "names() of identifier under caret"}, {"plot", "plot() of identifier under caret"},
            {"help", "help() of identifier under caret"}, {"head", "head() of identifier under caret"},
            {"tail", "tail() of identifier under caret"}, {"clear", "Clear STATghost Console"},
            {"close_graphics", "graphics.off()"}, {"remove_objects", "rm(list=ls())"},
            {"clear_all", "Clear Console, rm(list=ls()), graphics.off()"},
            {"assign", "Insert <-"}, {"pipe", "Insert pipe"}, {"outline", "Document outline"},
        };
        return lookup(map, key);
    }

    const char *ICON_FILE(const char *key)
    {
        static const std::unordered_map<std::string, const char *> map = {
            {"cfg", "setting-lines.png"}, {"arm", "idle.png"}, {"armed", "armed.png"},
            {"idle", "idle.png"}, {"host", "power.png"}, {"kill", "kill.png"},
            {"send", "send.png"}, {"function", "function.png"}, {"above", "above.png"},
            {"below", "below.png"}, {"chunk", "chunk.png"}, {"source", "export.png"},
            {"srcsel", "source-sel.png"}, {"setwd", "setwd.png"}, {"inspect", "print.png"},
            {"ls", "ls.png"}, {"str", "str.png"}, {"names", "names.png"}, {"plot", "plot.png"},
            {"help", "help_selected.png"}, {"head", "print_head.png"}, {"tail", "print_tail.png"},
            {"clear", "clear.png"}, {"close_graphics", "close_graphics.png"},
            {"remove_objects", "remove_objects.png"}, {"clear_all", "clear_all.png"},
            {"assign", "assign.png"}, {"pipe", "pipe.png"}, {"outline", "outline.png"},
        };
        return lookup(map, key);
    }

    const char *METHOD_NAME(const char *key)
    {
        static const std::unordered_map<std::string, const char *> map = {
            {"cfg", "config"}, {"arm", "toggle_arm"}, {"host", "toggle_host"},
            {"send", "send_selection"}, {"function", "send_function"}, {"above", "send_above"},
            {"below", "send_below"}, {"chunk", "send_chunk"}, {"source", "send_file"},
            {"srcsel", "source_selection"}, {"setwd", "set_wd_here"}, {"inspect", "inspect_print"},
            {"ls", "inspect_ls"}, {"str", "inspect_str"}, {"names", "inspect_names"},
            {"plot", "inspect_plot"}, {"help", "inspect_help"}, {"head", "inspect_head"},
            {"tail", "inspect_tail"}, {"clear", "clear_console"},
            {"close_graphics", "inspect_graphics_off"}, {"remove_objects", "inspect_rm_all"},
            {"clear_all", "inspect_clear_all"}, {"assign", "insert_assign"},
            {"pipe", "insert_pipe"}, {"outline", "show_outline"},
        };
        return lookup(map, key);
    }

    const char *nestParent(const char *key)
    {
        if (key == nullptr)
            return nullptr;
        for (std::size_t i = 0; i < sizeof(NEST_MENU) / sizeof(NEST_MENU[0]); ++i)
        {
            for (const char *const *child = NEST_CHILDREN[i]; *child != nullptr; ++child)
            {
                if (std::string(*child) == key)
                    return NEST_MENU[i].parent;
            }
        }
        return nullptr;
    }

    bool inDefaultShow(const char *key)
    {
        return StatghostPrefs::isChromeKeyVisible(key);
    }
}

const char *StatghostChrome::showKey(const std::size_t index)
{
    if (index >= SHOW_COUNT)
        return "cfg";
    return DEFAULT_SHOW[index];
}

const char *StatghostChrome::menuCaption(const char *key) { return MENU_CAP(key); }
const char *StatghostChrome::gridCaption(const char *key) { return GRID_CAP(key); }
const char *StatghostChrome::hintText(const char *key) { return HINT_TEXT(key); }
const char *StatghostChrome::iconFile(const char *key) { return ICON_FILE(key); }
const char *StatghostChrome::methodName(const char *key) { return METHOD_NAME(key); }

std::wstring StatghostChrome::menuPath(const char *key)
{
    const char *cap = MENU_CAP(key);
    for (const NestEntry &nest : NEST_MENU)
    {
        if (key != nullptr && std::string(nest.parent) == key)
        {
            return std::wstring(nest.label, nest.label + strlen(nest.label)) + L"\\" +
                   std::wstring(cap, cap + strlen(cap));
        }
    }
    const char *parent = nestParent(key);
    if (parent != nullptr)
    {
        for (const NestEntry &nest : NEST_MENU)
        {
            if (std::string(nest.parent) == parent)
            {
                return std::wstring(nest.label, nest.label + strlen(nest.label)) + L"\\" +
                       std::wstring(cap, cap + strlen(cap));
            }
        }
    }
    return std::wstring(cap, cap + strlen(cap));
}

std::vector<StatghostChrome::GridRow> StatghostChrome::gridPlan()
{
    std::vector<GridRow> plan;
    for (const GroupDef &group : GRID_GROUPS)
    {
        std::vector<const char *> part;
        for (const char *const *key = group.keys; *key != nullptr; ++key)
        {
            if (inDefaultShow(*key))
                part.push_back(*key);
        }
        if (part.empty())
            continue;

        GridRow header;
        header.kind = GridRowKind::Header;
        header.title = std::wstring(group.title, group.title + strlen(group.title));
        plan.push_back(header);

        for (std::size_t i = 0; i < part.size(); i += GRID_COLS)
        {
            GridRow row;
            row.kind = GridRowKind::Cells;
            const std::size_t end = (i + GRID_COLS < part.size()) ? i + GRID_COLS : part.size();
            row.keys.assign(part.begin() + static_cast<std::ptrdiff_t>(i),
                            part.begin() + static_cast<std::ptrdiff_t>(end));
            plan.push_back(row);
        }
    }
    return plan;
}
