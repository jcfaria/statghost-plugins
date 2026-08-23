/**
 * Icon FG picker — TypeScript port of cuda_statghost/icons_fg.py
 */

export type Rgb = readonly [number, number, number];

/** Closed white / mid gray / graphite — no hue. */
export const FG_WHITE: Rgb = [0xc4, 0xc4, 0xc4];
export const FG_GRAY: Rgb = [0x8a, 0x8a, 0x8a];
export const FG_GRAPHITE: Rgb = [0x3a, 0x3a, 0x3a];
const PALETTES: readonly Rgb[] = [FG_WHITE, FG_GRAY, FG_GRAPHITE];
const MIN_CONTRAST = 3.0;
const MODES = ['auto', 'light', 'dark', 'gray', 'theme'] as const;
export type IconFgMode = (typeof MODES)[number];
const ALIASES: Record<string, IconFgMode> = {
  white: 'light',
  graphite: 'dark',
  grey: 'gray',
  cinza: 'gray',
};

export function clampMode(raw: string | null | undefined): IconFgMode {
  let key = (raw ?? '').trim().toLowerCase();
  key = ALIASES[key] ?? key;
  if ((MODES as readonly string[]).includes(key)) {
    return key as IconFgMode;
  }
  return 'auto';
}

export function relLuma(rgb: Rgb): number {
  const [r, g, b] = rgb;
  return (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255.0;
}

export function contrastRatio(fg: Rgb, bg: Rgb): number {
  const l1 = relLuma(fg);
  const l2 = relLuma(bg);
  const lighter = Math.max(l1, l2);
  const darker = Math.min(l1, l2);
  return (lighter + 0.05) / (darker + 0.05);
}

export function pickFgRgb(
  mode: string | null | undefined,
  buttonFont: Rgb,
  bg: Rgb,
  candidates?: readonly Rgb[],
): Rgb {
  const m = clampMode(mode);
  if (m === 'light') {
    return FG_WHITE;
  }
  if (m === 'dark') {
    return FG_GRAPHITE;
  }
  if (m === 'gray') {
    return FG_GRAY;
  }
  if (m === 'theme') {
    return buttonFont;
  }

  const ordered: Rgb[] = [...PALETTES];
  if (candidates) {
    for (const c of candidates) {
      if (!ordered.some((o) => o[0] === c[0] && o[1] === c[1] && o[2] === c[2])) {
        ordered.push(c);
      }
    }
  }
  if (!ordered.some((o) => o[0] === buttonFont[0] && o[1] === buttonFont[1] && o[2] === buttonFont[2])) {
    ordered.push(buttonFont);
  }
  let best: Rgb | undefined;
  let bestRatio = 0;
  for (const cand of ordered) {
    const r = contrastRatio(cand, bg);
    if (r >= MIN_CONTRAST && r > bestRatio) {
      best = cand;
      bestRatio = r;
    }
  }
  if (best !== undefined) {
    return best;
  }
  if (relLuma(bg) < 0.45) {
    return FG_WHITE;
  }
  return FG_GRAPHITE;
}

export function rgbToCss(rgb: Rgb): string {
  return `rgb(${rgb[0]}, ${rgb[1]}, ${rgb[2]})`;
}
