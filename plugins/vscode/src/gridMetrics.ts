import type { GridLabelMode } from './chromeContract';
import { gridCellW } from './chromeContract';

/** Toolbar glyph tier — mirrors CudaText imagelist 16/24/32. */
export type IconSizePx = 16 | 24 | 32;

export const ICON_SIZE_TIERS: readonly IconSizePx[] = [16, 24, 32];

export interface GridMetrics {
  glyphPx: number;
  labelPx: number;
  /** Vertical gap between glyph and caption (below mode). */
  labelGap: number;
  cellPadV: number;
  cellPadH: number;
  /** Floor only — cells stretch to fill each 1/3 column (CudaText a_l/a_r). */
  cellMinW: Record<GridLabelMode, number>;
  cellMinH: Record<GridLabelMode, number>;
  bandMarginTop: number;
  bandPadV: number;
  bandPadH: number;
  bandFontPx: number;
  rowGap: number;
  bodyPadV: number;
  bodyPadH: number;
}

export function parseIconSize(raw: unknown): IconSizePx {
  const n = typeof raw === 'number' ? raw : parseInt(String(raw ?? ''), 10);
  if (n >= 32) {
    return 32;
  }
  if (n >= 24) {
    return 24;
  }
  return 16;
}

/** Compact keypad metrics scaled from CudaText _GRID_METRICS @ 16px. */
export function gridMetrics(iconPx: IconSizePx): GridMetrics {
  const scale = iconPx / 16;
  const labelPx = Math.max(8, Math.round(9 * scale));
  const cellPadV = Math.max(1, Math.round(2 * scale));
  const cellPadH = Math.max(1, Math.round(2 * scale));
  // Was a hard-coded 1px margin; +50% floor would be 2px, but the
  // webview still looked glued vs CudaText. 4px @ 16 (then 6 / 8).
  const labelGap = Math.max(4, Math.round(4 * scale));
  const captionH = labelPx + 1;
  const iconOnlyH = iconPx + cellPadV * 2;
  const belowH = iconPx + captionH + cellPadV * 2 + labelGap;
  // CudaText _GRID_METRICS placeholder widths before a_l/a_r stretch.
  const iconW = Math.round(26 * scale);
  const belowW = Math.max(Math.round(36 * scale), gridCellW());

  return {
    glyphPx: iconPx,
    labelPx,
    labelGap,
    cellPadV,
    cellPadH,
    cellMinW: {
      icon: iconW,
      below: belowW,
    },
    cellMinH: {
      icon: iconOnlyH,
      below: belowH,
    },
    bandMarginTop: Math.max(4, Math.round(6 * scale)),
    bandPadV: Math.max(1, Math.round(2 * scale)),
    bandPadH: Math.max(3, Math.round(4 * scale)),
    bandFontPx: Math.max(9, Math.round(10 * scale)),
    rowGap: 4,
    bodyPadV: Math.max(3, Math.round(4 * scale)),
    bodyPadH: 2,
  };
}

export function metricsCssVars(m: GridMetrics): string {
  return [
    `--sg-glyph:${m.glyphPx}px`,
    `--sg-label:${m.labelPx}px`,
    `--sg-label-gap:${m.labelGap}px`,
    `--sg-cell-pad-v:${m.cellPadV}px`,
    `--sg-cell-pad-h:${m.cellPadH}px`,
    `--sg-cell-min-icon:${m.cellMinH.icon}px`,
    `--sg-cell-min-below:${m.cellMinH.below}px`,
    `--sg-cell-min-w:${m.cellMinW.below}px`,
    `--sg-band-mt:${m.bandMarginTop}px`,
    `--sg-band-pad-v:${m.bandPadV}px`,
    `--sg-band-pad-h:${m.bandPadH}px`,
    `--sg-band-font:${m.bandFontPx}px`,
    `--sg-row-gap:${m.rowGap}px`,
    `--sg-body-pad-v:${m.bodyPadV}px`,
    `--sg-body-pad-h:${m.bodyPadH}px`,
  ].join(';');
}
