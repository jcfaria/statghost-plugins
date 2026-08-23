/**
 * Host-agnostic STATghost chrome contract — TypeScript port of
 * plugins/cudatext/cuda_statghost/chrome_show.py (keep in sync).
 * Canonical doc: shared/CHROME.md
 */

export const ACTION_KEYS = [
  'cfg', 'arm', 'host',
  'send', 'function', 'above', 'below', 'chunk',
  'source', 'srcsel', 'setwd',
  'inspect', 'ls', 'str', 'names', 'plot', 'help', 'head', 'tail',
  'clear', 'close_graphics', 'remove_objects', 'clear_all',
  'assign', 'pipe', 'outline',
] as const;

export type ActionKey = (typeof ACTION_KEYS)[number];

export const DEFAULT_SHOW: readonly ActionKey[] = [
  'cfg', 'arm', 'host',
  'send', 'function', 'above', 'below', 'chunk',
  'source', 'srcsel', 'setwd',
  'inspect', 'ls', 'str', 'names', 'plot', 'help', 'head', 'tail',
  'clear', 'close_graphics', 'remove_objects', 'clear_all',
];

export const NESTS: readonly (readonly [ActionKey, readonly ActionKey[]])[] = [
  ['send', ['function', 'above', 'below', 'chunk']],
  ['source', ['srcsel', 'setwd']],
  ['inspect', ['ls', 'str', 'names', 'plot', 'help', 'head', 'tail']],
  ['clear', ['close_graphics', 'remove_objects', 'clear_all']],
];

export const NEST_MENU: Readonly<Record<string, string>> = {
  send: 'Send',
  source: 'Source',
  inspect: 'Inspect',
  clear: 'Clear',
};

export const MENU_CAP: Readonly<Record<ActionKey, string>> = {
  cfg: 'Config',
  arm: 'Toggle Arm/Idle',
  host: 'Start/Quit STATghost',
  send: 'Send',
  function: 'Function',
  above: 'Above',
  below: 'Below',
  chunk: 'Chunk',
  source: 'Source',
  srcsel: 'Src sel',
  setwd: 'setwd',
  inspect: 'Print',
  ls: 'ls()',
  str: 'str()',
  names: 'names()',
  plot: 'plot()',
  help: 'Help',
  head: 'head()',
  tail: 'tail()',
  clear: 'Clear',
  close_graphics: 'graphics.off',
  remove_objects: 'rm all',
  clear_all: 'Clear all',
  assign: 'Insert <-',
  pipe: 'Insert pipe',
  outline: 'Outline…',
};

export const ACTION_METHODS: Readonly<Record<ActionKey, string>> = {
  cfg: 'config',
  arm: 'toggle_arm',
  host: 'toggle_host',
  send: 'send_selection',
  function: 'send_function',
  above: 'send_above',
  below: 'send_below',
  chunk: 'send_chunk',
  source: 'send_file',
  srcsel: 'source_selection',
  setwd: 'set_wd_here',
  inspect: 'inspect_print',
  ls: 'inspect_ls',
  str: 'inspect_str',
  names: 'inspect_names',
  plot: 'inspect_plot',
  help: 'inspect_help',
  head: 'inspect_head',
  tail: 'inspect_tail',
  clear: 'clear_console',
  close_graphics: 'inspect_graphics_off',
  remove_objects: 'inspect_rm_all',
  clear_all: 'inspect_clear_all',
  assign: 'insert_assign',
  pipe: 'insert_pipe',
  outline: 'show_outline',
};

export function nestParent(key: string): ActionKey | undefined {
  for (const [parent, kids] of NESTS) {
    if ((kids as readonly string[]).includes(key)) {
      return parent;
    }
  }
  return undefined;
}

export function menuPath(key: ActionKey): string {
  const cap = MENU_CAP[key] ?? key;
  if (key in NEST_MENU) {
    return `${NEST_MENU[key]}\\${cap}`;
  }
  const parent = nestParent(key);
  if (parent) {
    return `${NEST_MENU[parent]}\\${cap}`;
  }
  return cap;
}

export function collapseKeys(keys: readonly string[]): ActionKey[] {
  const present: ActionKey[] = [];
  const seen = new Set<string>();
  for (const key of keys) {
    if ((ACTION_KEYS as readonly string[]).includes(key) && !seen.has(key)) {
      present.push(key as ActionKey);
      seen.add(key);
    }
  }
  const hide = new Set<string>();
  const have = new Set(present);
  for (const [parent, kids] of NESTS) {
    if (have.has(parent)) {
      for (const k of kids) {
        if (have.has(k)) {
          hide.add(k);
        }
      }
    }
  }
  return present.filter((k) => !hide.has(k));
}

export const CLI_METHODS = new Set([
  'send_selection', 'send_function', 'send_above', 'send_below', 'send_chunk',
  'send_file', 'source_selection', 'set_wd_here',
  'inspect_print', 'inspect_ls', 'inspect_str', 'inspect_names',
  'inspect_plot', 'inspect_help', 'inspect_head', 'inspect_tail',
  'inspect_graphics_off', 'inspect_rm_all', 'inspect_clear_all',
  'clear_console',
]);

export const CYCLE_METHODS = new Set([
  'send_selection', 'inspect_ls', 'inspect_print', 'inspect_str',
  'inspect_names', 'inspect_head', 'inspect_tail', 'inspect_graphics_off',
  'set_wd_here', 'clear_console',
]);

export function encodeChecklist(showOn: Readonly<Record<string, boolean>>, keys: readonly string[]): string {
  const bits = keys.map((k) => (showOn[k] ? '1' : '0'));
  return `0;${bits.join(',')}`;
}

export function decodeChecklist(
  raw: string | null | undefined,
  keys: readonly string[],
  fallback?: Readonly<Record<string, boolean>>,
): Record<string, boolean> {
  let s = String(raw ?? '').trim();
  if (s.includes(';')) {
    s = s.split(';', 2)[1] ?? '';
  }
  const parts = s.split(',').map((p) => p.trim());
  if (parts.length < keys.length) {
    if (fallback !== undefined) {
      return { ...fallback };
    }
    return Object.fromEntries(keys.map((k) => [k, false]));
  }
  const out: Record<string, boolean> = {};
  keys.forEach((k, i) => {
    out[k] = ['1', 'true', 'yes', 'on'].includes(parts[i]);
  });
  return out;
}

const GROUP_HOST = new Set(['cfg', 'arm', 'host']);
const GROUP_SEND = new Set([
  'send', 'function', 'above', 'below', 'chunk',
  'source', 'srcsel', 'setwd',
  'inspect', 'ls', 'str', 'names', 'plot', 'help', 'head', 'tail',
  'clear', 'close_graphics', 'remove_objects', 'clear_all',
]);
const GROUP_EDIT = new Set(['assign', 'pipe', 'outline']);
const GROUPS = [GROUP_HOST, GROUP_SEND, GROUP_EDIT];

export function parseShow(raw: string | null | undefined, defaultKeys: readonly ActionKey[] = DEFAULT_SHOW): ActionKey[] {
  if (raw === null || raw === undefined) {
    return [...defaultKeys];
  }
  const text = String(raw).trim();
  if (text === '') {
    return [...defaultKeys];
  }
  const parts: ActionKey[] = [];
  for (const chunk of text.replace(/;/g, ',').replace(/ /g, ',').split(',')) {
    const key = chunk.trim().toLowerCase();
    if ((ACTION_KEYS as readonly string[]).includes(key) && !parts.includes(key as ActionKey)) {
      parts.push(key as ActionKey);
    }
  }
  if (parts.length === 0) {
    return [...defaultKeys];
  }
  return ACTION_KEYS.filter((k) => parts.includes(k));
}

export function formatShow(keys: readonly string[] | null | undefined): string {
  return parseShow((keys ?? []).join(','), []).join(',');
}

export function nestChildren(parent: string): readonly ActionKey[] {
  for (const [name, kids] of NESTS) {
    if (name === parent) {
      return kids;
    }
  }
  return [];
}

export function nestMenuKeys(parent: string, showKeys: readonly string[] | null | undefined): ActionKey[] {
  let show: Set<string>;
  if (showKeys === null || showKeys === undefined) {
    show = new Set(DEFAULT_SHOW);
  } else {
    const keys = [...showKeys];
    if (keys.length === 0) {
      return [];
    }
    show = new Set(parseShow(keys.join(','), []));
  }
  return nestChildren(parent).filter((k) => show.has(k));
}

export type ToolbarRow = readonly [string, string, string | null, string | null];

export function collapseNestedRows(tbRows: readonly ToolbarRow[]): ToolbarRow[] {
  const present = new Set(tbRows.filter((r) => r[2] !== null).map((r) => r[0]));
  const hide = new Set<string>();
  for (const [parent, kids] of NESTS) {
    if (present.has(parent)) {
      for (const k of kids) {
        if (present.has(k)) {
          hide.add(k);
        }
      }
    }
  }
  if (hide.size === 0) {
    return [...tbRows];
  }
  return tbRows.filter((row) => !hide.has(row[0]));
}

export function filterToolbarRows(tbRows: readonly ToolbarRow[], showKeys: readonly string[] | null | undefined): ToolbarRow[] {
  let show: Set<string>;
  if (showKeys === null || showKeys === undefined) {
    show = new Set(DEFAULT_SHOW);
  } else {
    const keys = [...showKeys];
    if (keys.length === 0) {
      return [];
    }
    show = new Set(parseShow(keys.join(','), []));
    if (show.size === 0) {
      return [];
    }
  }
  const actions = tbRows.filter((row) => row[2] !== null && show.has(row[0]));
  if (actions.length === 0) {
    return [];
  }
  const buckets: ToolbarRow[][] = [];
  for (const group of GROUPS) {
    const part = actions.filter((r) => group.has(r[0]));
    if (part.length > 0) {
      buckets.push(part);
    }
  }
  const out: ToolbarRow[] = [];
  if (tbRows.length > 0 && tbRows[0][2] === null) {
    out.push(tbRows[0]);
  }
  const seps = tbRows.filter((row) => row[2] === null);
  const midSeps = seps.length > 1 ? seps.slice(1) : [];
  buckets.forEach((part, i) => {
    if (i > 0) {
      if (i - 1 < midSeps.length) {
        out.push(midSeps[i - 1]);
      } else {
        out.push([`sep_${i}`, '-', null, null]);
      }
    }
    out.push(...part);
  });
  return out;
}

export function filterSideActions(
  sideRows: readonly (readonly [string, ...unknown[]])[],
  showKeys: readonly string[] | null | undefined,
): (readonly [string, ...unknown[]])[] {
  let show: Set<string>;
  if (showKeys === null || showKeys === undefined) {
    show = new Set(DEFAULT_SHOW);
  } else {
    const keys = [...showKeys];
    if (keys.length === 0) {
      return [];
    }
    show = new Set(parseShow(keys.join(','), []));
  }
  const rows = sideRows.filter((row) => show.has(row[0]));
  const keep = new Set<string>(collapseKeys(rows.map((r) => r[0])));
  return rows.filter((row) => keep.has(row[0]));
}

export function sideKeys(showKeys: readonly string[] | null | undefined): ActionKey[] {
  let wanted: Set<string>;
  if (showKeys === null || showKeys === undefined) {
    wanted = new Set(DEFAULT_SHOW);
  } else {
    const keys = [...showKeys];
    if (keys.length === 0) {
      return [];
    }
    wanted = new Set(parseShow(keys.join(','), []));
  }
  return collapseKeys(ACTION_KEYS.filter((k) => wanted.has(k)));
}

export const GRID_COLS = 3;

export const GRID_GROUPS: readonly (readonly ActionKey[])[] = [
  ['cfg', 'arm', 'host'],
  ['send', 'function', 'above', 'below', 'chunk'],
  ['source', 'srcsel', 'setwd'],
  ['inspect', 'ls', 'str', 'names', 'plot', 'help', 'head', 'tail'],
  ['clear', 'close_graphics', 'remove_objects', 'clear_all'],
  ['assign', 'pipe', 'outline'],
];

export const GRID_GROUP_TITLES = [
  'Host', 'Send', 'Source', 'Inspect', 'Clear', 'Edit',
] as const;

export const GRID_CAP: Readonly<Record<ActionKey, string>> = {
  cfg: 'Config',
  arm: 'Idle',
  host: 'Start',
  send: 'Send',
  function: 'Func',
  above: 'Above',
  below: 'Below',
  chunk: 'Chunk',
  source: 'Source',
  srcsel: 'Sel',
  setwd: 'setwd',
  inspect: 'Print',
  ls: 'ls',
  str: 'str',
  names: 'names',
  plot: 'plot',
  help: 'help',
  head: 'head',
  tail: 'tail',
  clear: 'Clear',
  close_graphics: 'g.off',
  remove_objects: 'rm',
  clear_all: 'all',
  assign: '<-',
  pipe: 'pipe',
  outline: 'out',
};

export const GRID_CAP_SLACK = 1.2;
export const GRID_EMU_CHAR = 7;
export const GRID_CELL_MIN = 36;

/** Min keypad cell width: longest caption × em × 1.20 (CudaText grid_cell_w). */
export function gridCellW(caps?: readonly string[]): number {
  const vals = caps ?? Object.values(GRID_CAP);
  let n = 1;
  for (const c of vals) {
    if (c.length > n) {
      n = c.length;
    }
  }
  return Math.max(GRID_CELL_MIN, Math.round(n * GRID_EMU_CHAR * GRID_CAP_SLACK));
}

export const GRID_LABEL_DEFAULT = 'below';
export const GRID_LABELS = ['below', 'icon'] as const;
export type GridLabelMode = (typeof GRID_LABELS)[number];

export function parseGridLabel(raw: string | null | undefined): GridLabelMode {
  const aliases: Record<string, GridLabelMode> = {
    under: 'below',
    vert: 'below',
    vertical: 'below',
    only: 'icon',
    icons: 'icon',
    horz: 'icon',
    horiz: 'icon',
    side: 'icon',
    beside: 'icon',
  };
  let key = (raw ?? '').trim().toLowerCase();
  key = aliases[key] ?? key;
  if ((GRID_LABELS as readonly string[]).includes(key)) {
    return key as GridLabelMode;
  }
  return GRID_LABEL_DEFAULT;
}

export function gridKeys(): readonly ActionKey[] {
  return ACTION_KEYS;
}

export type GridPlanEntry =
  | readonly ['hdr', string]
  | readonly ['row', readonly ActionKey[]];

export function gridPlan(keys?: readonly string[] | null, cols = GRID_COLS): GridPlanEntry[] {
  if (cols < 1) {
    cols = GRID_COLS;
  }
  const wanted = keys === null || keys === undefined
    ? new Set(ACTION_KEYS)
    : new Set(ACTION_KEYS.filter((k) => new Set(keys).has(k)));
  const plan: GridPlanEntry[] = [];
  for (let i = 0; i < GRID_GROUPS.length; i++) {
    const group = GRID_GROUPS[i];
    const title = GRID_GROUP_TITLES[i];
    const part = group.filter((k) => wanted.has(k));
    if (part.length === 0) {
      continue;
    }
    plan.push(['hdr', title]);
    for (let j = 0; j < part.length; j += cols) {
      plan.push(['row', part.slice(j, j + cols)]);
    }
  }
  return plan;
}

export function commandIdForKey(key: ActionKey): string {
  return `statghost.${key}`;
}

export function keyFromCommandId(commandId: string): ActionKey | undefined {
  const prefix = 'statghost.';
  if (!commandId.startsWith(prefix)) {
    return undefined;
  }
  const key = commandId.slice(prefix.length);
  if ((ACTION_KEYS as readonly string[]).includes(key)) {
    return key as ActionKey;
  }
  return undefined;
}
