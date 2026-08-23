import * as assert from 'assert';
import * as vscode from 'vscode';

export async function run(): Promise<void> {
  const extId = 'jcfaria.statghost-vscode';
  const ext = vscode.extensions.getExtension(extId);
  assert.ok(ext, `extension ${extId} not found`);
  await ext.activate();

  const cmds = await vscode.commands.getCommands(true);
  const required = [
    'statghost.send',
    'statghost.arm',
    'statghost.host',
    'statghost.cfg',
    'statghost.clear',
    'statghost.inspect',
  ];
  for (const id of required) {
    assert.ok(cmds.includes(id), `missing command ${id}`);
  }
}
