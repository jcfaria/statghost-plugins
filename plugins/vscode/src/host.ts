import * as fs from 'fs';
import * as path from 'path';
import { spawn } from 'child_process';
import * as vscode from 'vscode';
import { getHostExe } from './prefs';

const WIN = process.platform === 'win32';

function exeName(): string {
  return WIN ? 'statghost.exe' : 'statghost';
}

function isExe(filePath: string): boolean {
  if (!filePath) {
    return false;
  }
  const p = path.resolve(filePath);
  if (!fs.existsSync(p) || !fs.statSync(p).isFile()) {
    return false;
  }
  if (WIN) {
    return true;
  }
  try {
    fs.accessSync(p, fs.constants.X_OK);
    return true;
  } catch {
    return false;
  }
}

function siblingStatghostOut(): string {
  // Walk up from extension to find sibling statghost/src/_out/
  let cur = path.dirname(__dirname);
  for (let i = 0; i < 8; i++) {
    const parent = path.dirname(cur);
    if (parent === cur) {
      break;
    }
    const cand = path.join(parent, 'statghost', 'src', '_out', exeName());
    if (isExe(cand)) {
      return cand;
    }
    cur = parent;
  }
  return '';
}

export function findExe(): string {
  const cfg = getHostExe();
  if (isExe(cfg)) {
    return path.resolve(cfg);
  }
  const env = (process.env.STATGHOST_EXE ?? '').trim();
  if (isExe(env)) {
    return path.resolve(env);
  }
  const sib = siblingStatghostOut();
  if (isExe(sib)) {
    return sib;
  }
  return '';
}

export async function startHost(): Promise<boolean> {
  const exe = findExe();
  if (!exe) {
    void vscode.window.showErrorMessage(
      'STATghost: executable not found — set statghost.host.exe or install sibling statghost clone.',
    );
    return false;
  }
  try {
    const child = spawn(exe, [], { detached: true, stdio: 'ignore' });
    child.unref();
    void vscode.window.setStatusBarMessage(`STATghost: started ${exe}`);
    return true;
  } catch (e) {
    void vscode.window.showErrorMessage(`STATghost: cannot start — ${String(e)}`);
    return false;
  }
}

export async function toggleHost(running: boolean): Promise<void> {
  if (running) {
    const { quitHost } = await import('./bridge');
    await quitHost();
  } else {
    await startHost();
  }
}
