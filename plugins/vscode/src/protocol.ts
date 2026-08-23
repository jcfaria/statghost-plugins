/**
 * Clipboard contract — TypeScript port of cuda_statghost/protocol.py
 */

export const PREFIX = '#. STATGHOST:';

export const CMD_TOGGLE_ARM = 'TOGGLE_ARM';
export const CMD_ARM = 'ARM';
export const CMD_IDLE = 'IDLE';
export const CMD_EVAL = 'EVAL';
export const CMD_EVAL_KEEP = 'EVAL_KEEP';
export const CMD_QUIT = 'QUIT';
export const CMD_CLEAR = 'CLEAR';

let counter = 0;

function nonce(): string {
  counter += 1;
  let ns: bigint;
  if (typeof process !== 'undefined' && typeof process.hrtime?.bigint === 'function') {
    ns = process.hrtime.bigint();
  } else {
    ns = BigInt(Date.now()) * 1_000_000n;
  }
  return `${ns}-${counter}`;
}

export function nextArmCmd(pluginShowsArmed: boolean): string {
  return pluginShowsArmed ? CMD_IDLE : CMD_ARM;
}

export function makeCommand(name: string): string {
  const cmd = (name ?? '').trim().toUpperCase();
  return `${PREFIX}${cmd} ${nonce()}`;
}

export function makeEval(code: string | null | undefined, keepFocus = false): string {
  const cmd = keepFocus ? CMD_EVAL_KEEP : CMD_EVAL;
  return `${makeCommand(cmd)}\n${code ?? ''}`;
}

export function parseMessage(text: string | null | undefined): { cmd: string | null; body: string | null } {
  let raw = text ?? '';
  if (raw.startsWith('\ufeff')) {
    raw = raw.slice(1);
  }
  const nl = raw.indexOf('\n');
  let head: string;
  let body: string;
  if (nl < 0) {
    head = raw;
    body = '';
  } else {
    head = raw.slice(0, nl);
    body = raw.slice(nl + 1);
  }
  if (head.endsWith('\r')) {
    head = head.slice(0, -1);
  }
  head = head.trim();
  if (!head.startsWith(PREFIX)) {
    return { cmd: null, body: null };
  }
  let tail = head.slice(PREFIX.length).trim();
  if (!tail) {
    return { cmd: null, body: null };
  }
  const sp = tail.indexOf(' ');
  const cmd = (sp < 0 ? tail : tail.slice(0, sp)).toUpperCase();
  if (!cmd) {
    return { cmd: null, body: null };
  }
  return { cmd, body };
}
