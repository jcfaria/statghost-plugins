import * as vscode from 'vscode';

/** Active editor text helpers — subset of cuda_statghost/editor.py for v1. */

export function activeEditor(): vscode.TextEditor | undefined {
  return vscode.window.activeTextEditor;
}

export function selectionText(ed?: vscode.TextEditor): string {
  const editor = ed ?? activeEditor();
  if (!editor) {
    return '';
  }
  return editor.document.getText(editor.selection);
}

export function caretLineIndex(ed?: vscode.TextEditor): number | undefined {
  const editor = ed ?? activeEditor();
  if (!editor) {
    return undefined;
  }
  return editor.selection.active.line;
}

export function lineCount(ed?: vscode.TextEditor): number {
  const editor = ed ?? activeEditor();
  if (!editor) {
    return 0;
  }
  return editor.document.lineCount;
}

export function getLine(line: number, ed?: vscode.TextEditor): string {
  const editor = ed ?? activeEditor();
  if (!editor || line < 0 || line >= editor.document.lineCount) {
    return '';
  }
  return editor.document.lineAt(line).text;
}

export function linesFromStart(toLine: number, ed?: vscode.TextEditor): string {
  const editor = ed ?? activeEditor();
  if (!editor) {
    return '';
  }
  const end = Math.min(toLine, editor.document.lineCount - 1);
  const lines: string[] = [];
  for (let i = 0; i <= end; i++) {
    lines.push(editor.document.lineAt(i).text);
  }
  return lines.join('\n');
}

export function linesToEnd(fromLine: number, ed?: vscode.TextEditor): string {
  const editor = ed ?? activeEditor();
  if (!editor) {
    return '';
  }
  const start = Math.max(0, fromLine);
  const lines: string[] = [];
  for (let i = start; i < editor.document.lineCount; i++) {
    lines.push(editor.document.lineAt(i).text);
  }
  return lines.join('\n');
}

/** R identifier under caret — simplified rword.py v1. */
export function identifierAtCaret(ed?: vscode.TextEditor): string {
  const editor = ed ?? activeEditor();
  if (!editor) {
    return '';
  }
  const pos = editor.selection.active;
  const line = editor.document.lineAt(pos.line).text;
  const re = /[A-Za-z._][A-Za-z0-9._]*/g;
  let match: RegExpExecArray | null;
  while ((match = re.exec(line)) !== null) {
    const start = match.index;
    const end = start + match[0].length;
    if (pos.character >= start && pos.character <= end) {
      return match[0];
    }
  }
  return '';
}

export function insertAtCaret(text: string, ed?: vscode.TextEditor): boolean {
  const editor = ed ?? activeEditor();
  if (!editor) {
    return false;
  }
  void editor.edit((eb) => {
    eb.insert(editor.selection.active, text);
  });
  return true;
}

export function documentPath(ed?: vscode.TextEditor): string {
  const editor = ed ?? activeEditor();
  if (!editor || editor.document.uri.scheme !== 'file') {
    return '';
  }
  return editor.document.uri.fsPath;
}

export function isBlankOrHashComment(line: string): boolean {
  const s = (line || '').trim();
  return s === '' || s.startsWith('#');
}

/** Last line index of a real selection, or undefined when caret-only. */
export function selectionLastLine(ed?: vscode.TextEditor): number | undefined {
  const editor = ed ?? activeEditor();
  if (!editor) {
    return undefined;
  }
  const { selection } = editor;
  if (selection.isEmpty) {
    return undefined;
  }
  const anchor = selection.anchor;
  const active = selection.active;
  const forward = anchor.line < active.line
    || (anchor.line === active.line && anchor.character <= active.character);
  const endLine = forward ? active.line : anchor.line;
  const endChar = forward ? active.character : anchor.character;
  if (endChar === 0 && endLine > (forward ? anchor.line : active.line)) {
    return endLine - 1;
  }
  return endLine;
}

/** Column 0 of next code line; skip blanks and # comments. EOF: stay. */
export function advanceCaretAfter(fromLine: number, ed?: vscode.TextEditor): void {
  const editor = ed ?? activeEditor();
  if (!editor) {
    return;
  }
  const n = editor.document.lineCount;
  let y = fromLine + 1;
  while (y < n) {
    if (!isBlankOrHashComment(editor.document.lineAt(y).text)) {
      const pos = new vscode.Position(y, 0);
      editor.selection = new vscode.Selection(pos, pos);
      editor.revealRange(new vscode.Range(pos, pos));
      return;
    }
    y += 1;
  }
}
