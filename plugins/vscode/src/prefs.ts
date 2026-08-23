import * as vscode from 'vscode';
import {
  DEFAULT_SHOW,
  parseGridLabel,
  parseShow,
  type ActionKey,
  type GridLabelMode,
} from './chromeContract';
import { clampMode, type IconFgMode } from './iconsFg';
import { parseIconSize, type IconSizePx } from './gridMetrics';

export function getChromeShow(): ActionKey[] {
  const raw = vscode.workspace.getConfiguration('statghost').get<string>('chrome.show', '');
  return parseShow(raw);
}

export function getGridLabel(): GridLabelMode {
  const raw = vscode.workspace.getConfiguration('statghost').get<string>('chrome.gridLabel', 'below');
  return parseGridLabel(raw);
}

export function getIconsFg(): IconFgMode {
  const raw = vscode.workspace.getConfiguration('statghost').get<string>('icons.fg', 'auto');
  return clampMode(raw);
}

export function getIconsSize(): IconSizePx {
  const raw = vscode.workspace.getConfiguration('statghost').get<number>('icons.size', 16);
  return parseIconSize(raw);
}

export function getHostExe(): string {
  return (vscode.workspace.getConfiguration('statghost').get<string>('host.exe', '') ?? '').trim();
}

export function defaultShowCsv(): string {
  return DEFAULT_SHOW.join(',');
}
