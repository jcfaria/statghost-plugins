/**
 * VS Code theme token bridge — mirrors cuda_statghost/chrome.py _hdr_band_bg
 * and icons.py theme_rgb using CSS variables in the webview.
 */

import type { Rgb } from './iconsFg';
import { pickFgRgb, rgbToCss } from './iconsFg';

export function parseCssColor(css: string | undefined, fallback: Rgb): Rgb {
  if (!css) {
    return fallback;
  }
  const s = css.trim();
  const hex = /^#([0-9a-f]{3}|[0-9a-f]{6}|[0-9a-f]{8})$/i.exec(s);
  if (hex) {
    let h = hex[1];
    if (h.length === 3) {
      h = h.split('').map((c) => c + c).join('');
    }
    if (h.length >= 6) {
      return [
        parseInt(h.slice(0, 2), 16),
        parseInt(h.slice(2, 4), 16),
        parseInt(h.slice(4, 6), 16),
      ];
    }
  }
  const rgb = /^rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)/i.exec(s);
  if (rgb) {
    return [parseInt(rgb[1], 10), parseInt(rgb[2], 10), parseInt(rgb[3], 10)];
  }
  return fallback;
}

function blendRgb(a: Rgb, b: Rgb, t: number): Rgb {
  return [
    Math.round(a[0] + (b[0] - a[0]) * t),
    Math.round(a[1] + (b[1] - a[1]) * t),
    Math.round(a[2] + (b[2] - a[2]) * t),
  ];
}

/** Slight stripe lift/dip vs TabBg — BG only, not caption colour. */
export function hdrBandBg(back: Rgb, face: Rgb, border: Rgb): Rgb {
  const luma = (0.2126 * back[0] + 0.7152 * back[1] + 0.0722 * back[2]) / 255.0;
  if (luma < 0.45) {
    const lift: Rgb = (face[0] !== back[0] || face[1] !== back[1] || face[2] !== back[2])
      ? face
      : [0x52, 0x52, 0x56];
    return blendRgb(back, lift, 0.58);
  }
  const shade: Rgb = (border[0] !== back[0] || border[1] !== back[1] || border[2] !== back[2])
    ? border
    : [0xc8, 0xc8, 0xcc];
  return blendRgb(back, shade, 0.32);
}

export interface ThemeSnapshot {
  tabBg: Rgb;
  buttonBg: Rgb;
  tabFont: Rgb;
  buttonFont: Rgb;
  border: Rgb;
  hdrBand: Rgb;
  /** Sidebar surface — cells are transparent; used for icon FG contrast. */
  cellBg: Rgb;
  cellFg: Rgb;
}

/** Build theme snapshot from VS Code CSS variable values (read in webview). */
export function themeFromCssVars(vars: Record<string, string | undefined>, iconsFgMode: string): ThemeSnapshot {
  const tabBg = parseCssColor(vars.tabBg, [0x2a, 0x2a, 0x2a]);
  const buttonBg = parseCssColor(vars.buttonBg, tabBg);
  const tabFont = parseCssColor(vars.tabFont, [0x90, 0x90, 0x90]);
  const buttonFont = parseCssColor(vars.buttonFont, tabFont);
  const border = parseCssColor(vars.border, [0x60, 0x60, 0x60]);
  const hdrBand = hdrBandBg(tabBg, buttonBg, border);
  const cellBg = tabBg;
  const cellFg = pickFgRgb(iconsFgMode, buttonFont, cellBg, [tabFont]);
  return { tabBg, buttonBg, tabFont, buttonFont, border, hdrBand, cellFg, cellBg };
}

export function themeCssBlock(snapshot: ThemeSnapshot): string {
  const h = rgbToCss(snapshot.hdrBand);
  const cellFg = rgbToCss(snapshot.cellFg);
  const tabFont = rgbToCss(snapshot.tabFont);
  return `
    --sg-hdr-band: ${h};
    --sg-cell-fg: ${cellFg};
    --sg-hdr-fg: ${tabFont};
  `;
}

/** CSS variable names the webview reads from getComputedStyle(document.body). */
export const VSCODE_CSS_VARS = [
  '--vscode-tab-activeBackground',
  '--vscode-sideBar-background',
  '--vscode-editor-background',
  '--vscode-button-secondaryBackground',
  '--vscode-tab-activeForeground',
  '--vscode-button-secondaryForeground',
  '--vscode-foreground',
  '--vscode-panel-border',
] as const;

export function mapVscodeVars(computed: Record<string, string>): Record<string, string | undefined> {
  return {
    tabBg: computed['--vscode-tab-activeBackground']
      ?? computed['--vscode-sideBar-background']
      ?? computed['--vscode-editor-background'],
    buttonBg: computed['--vscode-button-secondaryBackground']
      ?? computed['--vscode-tab-activeBackground']
      ?? computed['--vscode-sideBar-background'],
    tabFont: computed['--vscode-tab-activeForeground'] ?? computed['--vscode-foreground'],
    buttonFont: computed['--vscode-button-secondaryForeground'] ?? computed['--vscode-foreground'],
    border: computed['--vscode-panel-border'],
  };
}
