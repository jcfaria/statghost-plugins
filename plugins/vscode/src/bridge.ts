import * as vscode from 'vscode';
import {
  CMD_CLEAR,
  CMD_QUIT,
  makeCommand,
  makeEval,
  nextArmCmd,
} from './protocol';

const PLUGIN = 'STATghost';

export async function writeClipboard(text: string): Promise<void> {
  await vscode.env.clipboard.writeText(text);
}

export async function sendCommand(name: string, hint: string): Promise<void> {
  await writeClipboard(makeCommand(name));
  void vscode.window.setStatusBarMessage(`${PLUGIN}: ${hint}`);
}

export async function sendEval(
  code: string,
  mode: string,
  keepFocus?: boolean,
): Promise<boolean> {
  if (!code || code.trim() === '') {
    void vscode.window.showInformationMessage(`${PLUGIN}: nothing to send (${mode})`);
    return false;
  }
  const kf = keepFocus ?? vscode.workspace.getConfiguration('statghost').get<boolean>('send.keepFocus', true);
  await writeClipboard(makeEval(code, kf));
  void vscode.window.setStatusBarMessage(
    `${PLUGIN}: sent ${mode} (${code.length} chars) — STATghost must be Armed`,
  );
  return true;
}

export class ArmState {
  private armed = false;

  isArmed(): boolean {
    return this.armed;
  }

  async toggle(): Promise<void> {
    const cmd = nextArmCmd(this.armed);
    await sendCommand(cmd, this.armed ? 'Idle' : 'Arm');
    this.armed = !this.armed;
  }

  setArmed(value: boolean): void {
    this.armed = value;
  }
}

export async function quitHost(): Promise<void> {
  await sendCommand(CMD_QUIT, 'Quit STATghost');
}

export async function clearConsole(): Promise<void> {
  await sendCommand(CMD_CLEAR, 'Clear Console');
}
