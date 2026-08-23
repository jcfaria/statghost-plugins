import * as vscode from 'vscode';
import { ArmState } from './bridge';
import { registerCommands } from './commands';
import { AnalyticPanelProvider } from './panelProvider';

export function activate(context: vscode.ExtensionContext): void {
  const armState = new ArmState();

  const panelProvider = new AnalyticPanelProvider(context.extensionUri, armState);
  context.subscriptions.push(
    vscode.window.registerWebviewViewProvider(
      AnalyticPanelProvider.viewType,
      panelProvider,
      { webviewOptions: { retainContextWhenHidden: true } },
    ),
  );

  const refreshPanel = () => panelProvider.refresh();
  registerCommands(context, armState, refreshPanel);

  context.subscriptions.push(
    vscode.workspace.onDidChangeConfiguration((e) => {
      if (
        e.affectsConfiguration('statghost.chrome.show')
        || e.affectsConfiguration('statghost.chrome.gridLabel')
        || e.affectsConfiguration('statghost.icons.fg')
        || e.affectsConfiguration('statghost.icons.size')
      ) {
        refreshPanel();
      }
    }),
  );

  void vscode.window.setStatusBarMessage('STATghost extension active');
}

export function deactivate(): void {
  // no-op
}
