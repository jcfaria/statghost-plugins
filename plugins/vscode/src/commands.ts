import * as path from 'path';
import * as vscode from 'vscode';
import type { ActionKey } from './chromeContract';
import { ACTION_METHODS, commandIdForKey } from './chromeContract';
import { ArmState, clearConsole, sendCommand, sendEval } from './bridge';
import * as ed from './editor';
import { startHost, toggleHost } from './host';
import { CMD_CLEAR } from './protocol';
import { statementAtCaret } from './statement';

const PLUGIN = 'STATghost';

function rQuote(p: string): string {
  const s = (p ?? '').replace(/\\/g, '/');
  return `"${s.replace(/"/g, '\\"')}"`;
}

export function registerCommands(
  context: vscode.ExtensionContext,
  armState: ArmState,
  onPanelRefresh?: () => void,
): void {
  const handlers: Record<string, () => void | Promise<void>> = {
    config: async () => {
      await vscode.commands.executeCommand(
        'workbench.action.openSettings',
        '@ext:jcfaria.statghost-vscode',
      );
    },
    toggle_arm: async () => {
      await armState.toggle();
      onPanelRefresh?.();
    },
    toggle_host: async () => {
      // v1: start if not configured running detection; quit via clipboard
      const pick = await vscode.window.showQuickPick(
        ['Start STATghost', 'Quit STATghost'],
        { title: PLUGIN },
      );
      if (pick === 'Start STATghost') {
        await startHost();
      } else if (pick === 'Quit STATghost') {
        await toggleHost(true);
      }
      onPanelRefresh?.();
    },
    send_selection: async () => {
      const editor = ed.activeEditor();
      const sel = ed.selectionText(editor);
      if (sel.trim() !== '') {
        const last = ed.selectionLastLine(editor);
        if (await sendEval(sel, 'selection') && last !== undefined) {
          ed.advanceCaretAfter(last, editor);
        }
        return;
      }
      const y = ed.caretLineIndex(editor);
      if (y === undefined) {
        void vscode.window.showInformationMessage(`${PLUGIN}: nothing to send`);
        return;
      }
      const n = ed.lineCount(editor);
      const getLine = (i: number) => ed.getLine(i, editor);
      const { end, text, mode } = statementAtCaret(y, getLine, n);
      if (!text.trim()) {
        void vscode.window.showInformationMessage(`${PLUGIN}: nothing to send`);
        return;
      }
      if (await sendEval(text, mode) && end !== null) {
        ed.advanceCaretAfter(end, editor);
      }
    },
    send_function: async () => {
      void vscode.window.showInformationMessage(
        `${PLUGIN}: send_function — enclosing-function parse not yet ported (v1 stub)`,
      );
    },
    send_above: async () => {
      const editor = ed.activeEditor();
      const y = ed.caretLineIndex(editor);
      if (y === undefined) {
        return;
      }
      if (await sendEval(ed.linesFromStart(y, editor), 'above')) {
        ed.advanceCaretAfter(y, editor);
      }
    },
    send_below: async () => {
      const y = ed.caretLineIndex();
      if (y === undefined) {
        return;
      }
      await sendEval(ed.linesToEnd(y), 'below');
    },
    send_chunk: async () => {
      void vscode.window.showInformationMessage(`${PLUGIN}: send_chunk — sniper chunk not yet ported (v1 stub)`);
    },
    send_file: async () => {
      void vscode.window.showInformationMessage(
        `${PLUGIN}: send_file — .paths[4] slot write not yet ported (v1 stub)`,
      );
    },
    source_selection: async () => {
      void vscode.window.showInformationMessage(
        `${PLUGIN}: source_selection — .paths[5] not yet ported (v1 stub)`,
      );
    },
    set_wd_here: async () => {
      const p = ed.documentPath();
      if (!p) {
        void vscode.window.showInformationMessage(`${PLUGIN}: save the file first (setwd)`);
        return;
      }
      const folder = path.dirname(p);
      await sendEval(`setwd(${rQuote(folder)})`, 'setwd');
    },
    inspect_print: async () => {
      const id = ed.identifierAtCaret();
      if (!id) {
        void vscode.window.showInformationMessage(`${PLUGIN}: no identifier to print`);
        return;
      }
      await sendEval(id, 'print');
    },
    inspect_ls: async () => {
      await sendEval('ls()', 'ls');
    },
    inspect_str: async () => {
      const id = ed.identifierAtCaret();
      await sendEval(id ? `str(${id})` : 'str()', 'str');
    },
    inspect_names: async () => {
      const id = ed.identifierAtCaret();
      await sendEval(id ? `names(${id})` : 'names()', 'names');
    },
    inspect_plot: async () => {
      const id = ed.identifierAtCaret();
      await sendEval(id ? `plot(${id})` : 'plot()', 'plot');
    },
    inspect_help: async () => {
      const id = ed.identifierAtCaret();
      if (!id) {
        void vscode.window.showInformationMessage(`${PLUGIN}: no identifier for help()`);
        return;
      }
      await sendEval(`help(${id})`, 'help');
    },
    inspect_head: async () => {
      const id = ed.identifierAtCaret();
      await sendEval(id ? `head(${id})` : 'head()', 'head');
    },
    inspect_tail: async () => {
      const id = ed.identifierAtCaret();
      await sendEval(id ? `tail(${id})` : 'tail()', 'tail');
    },
    clear_console: async () => clearConsole(),
    inspect_graphics_off: async () => {
      await sendEval('graphics.off()', 'graphics.off');
    },
    inspect_rm_all: async () => {
      await sendEval('rm(list=ls())', 'rm all');
    },
    inspect_clear_all: async () => {
      await sendCommand(CMD_CLEAR, 'Clear all prelude');
      await sendEval('rm(list=ls())\ngraphics.off()', 'clear all');
    },
    insert_assign: async () => {
      ed.insertAtCaret(' <- ');
    },
    insert_pipe: async () => {
      ed.insertAtCaret(' |> ');
    },
    show_outline: async () => {
      void vscode.window.showInformationMessage(`${PLUGIN}: outline — not embedded (D29)`);
    },
  };

  for (const key of Object.keys(ACTION_METHODS) as ActionKey[]) {
    const method = ACTION_METHODS[key];
    const commandId = commandIdForKey(key);
    const handler = handlers[method];
    if (!handler) {
      continue;
    }
    context.subscriptions.push(
      vscode.commands.registerCommand(commandId, handler),
    );
  }
}
