/**
 * Action id → PNG filename (cuda_statghost/chrome.py _TB).
 * Glyphs: media/res/{16,24,32}px/ (copy of shared/res).
 */

import type { ActionKey } from './chromeContract';

export const ICON_FILES: Readonly<Record<ActionKey, string>> = {
  cfg: 'setting-lines.png',
  arm: 'idle.png',
  host: 'power.png',
  send: 'send.png',
  function: 'function.png',
  above: 'above.png',
  below: 'below.png',
  chunk: 'chunk.png',
  source: 'export.png',
  srcsel: 'source-sel.png',
  setwd: 'setwd.png',
  inspect: 'print.png',
  ls: 'ls.png',
  str: 'str.png',
  names: 'names.png',
  plot: 'plot.png',
  help: 'help_selected.png',
  head: 'print_head.png',
  tail: 'print_tail.png',
  clear: 'clear.png',
  close_graphics: 'close_graphics.png',
  remove_objects: 'remove_objects.png',
  clear_all: 'clear_all.png',
  assign: 'assign.png',
  pipe: 'pipe.png',
  outline: 'outline.png',
};

export const ACTION_HINTS: Readonly<Partial<Record<ActionKey, string>>> = {
  cfg: 'STATghost plugin Config',
  arm: 'Toggle Arm/Idle',
  host: 'Start/Quit STATghost',
  send: 'Send selection, enclosing function, or statement',
  function: 'Send enclosing function',
  above: 'Send above (start→caret)',
  below: 'Send below (caret→EOF)',
  chunk: 'Send sniper chunk',
  source: 'Source file via .paths[4]',
  srcsel: 'Source selection / function via .paths[5]',
  setwd: 'setwd to file directory',
  inspect: 'Print identifier under caret (Inspect extras in the arrow)',
  ls: 'ls()',
  str: 'str() of identifier under caret',
  names: 'names() of identifier under caret',
  plot: 'plot() of identifier under caret',
  help: 'help() of identifier under caret',
  head: 'head() of identifier under caret',
  tail: 'tail() of identifier under caret',
  clear: 'Clear STATghost Console',
  close_graphics: 'graphics.off()',
  remove_objects: 'rm(list=ls())',
  clear_all: 'Clear Console, rm(list=ls()), graphics.off()',
  assign: 'Insert <-',
  pipe: 'Insert pipe',
  outline: 'Document outline',
};
