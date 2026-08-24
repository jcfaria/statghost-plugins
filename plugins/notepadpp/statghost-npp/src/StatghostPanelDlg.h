#pragma once

#include "DockingDlgInterface.h"
#include "resource.h"

#include <string>
#include <unordered_map>
#include <vector>

class StatghostPanelDlg : public DockingDlgInterface
{
public:
    StatghostPanelDlg();

    void setParent(HWND parent) { _hParent = parent; }
    void refreshArmCaption();
    void refreshHostCaption();
    void refreshDynamicCaptions();
    void rebuildGrid();
    void display() { DockingDlgInterface::display(true); }

protected:
    INT_PTR CALLBACK run_dlgProc(UINT message, WPARAM wParam, LPARAM lParam) override;

private:
    struct CellControl
    {
        HWND header = nullptr;
        HWND button = nullptr;
        HWND caption = nullptr;
        const char *key = nullptr;
    };

    void destroyGrid();
    void buildGrid();
    void layoutGrid(int width, int height);
    void applyTheme();

    std::vector<CellControl> _cells;
    std::unordered_map<int, const char *> _btnKeys;
    int _scrollY = 0;
    int _contentHeight = 0;
    bool _gridBuilt = false;
};
