import * as path from 'path';
import { runTests } from '@vscode/test-electron';

async function main(): Promise<void> {
  const extensionDevelopmentPath = path.resolve(__dirname, '../../');
  const extensionTestsPath = path.resolve(__dirname, './suite/index');

  try {
    const exitCode = await runTests({
      extensionDevelopmentPath,
      extensionTestsPath,
      launchArgs: ['--disable-extensions'],
    });
    process.exit(exitCode);
  } catch (err) {
    console.error('Failed to run extension integration tests:', err);
    process.exit(1);
  }
}

main();
