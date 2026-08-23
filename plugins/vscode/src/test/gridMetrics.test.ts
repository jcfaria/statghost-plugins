import { strict as assert } from 'node:assert';
import { describe, it } from 'node:test';
import { gridMetrics, metricsCssVars, parseIconSize } from '../gridMetrics';
import { gridCellW } from '../chromeContract';

describe('gridMetrics', () => {
  it('parseIconSize clamps to 16/24/32', () => {
    assert.equal(parseIconSize(16), 16);
    assert.equal(parseIconSize(24), 24);
    assert.equal(parseIconSize(32), 32);
    assert.equal(parseIconSize(20), 16);
    assert.equal(parseIconSize(28), 24);
    assert.equal(parseIconSize('24'), 24);
    assert.equal(parseIconSize(''), 16);
  });

  it('tiers scale glyph and below cell height', () => {
    const s16 = gridMetrics(16);
    const s24 = gridMetrics(24);
    const s32 = gridMetrics(32);
    assert.equal(s16.glyphPx, 16);
    assert.equal(s24.glyphPx, 24);
    assert.equal(s32.glyphPx, 32);
    assert.ok(s16.cellMinH.below < s24.cellMinH.below);
    assert.ok(s24.cellMinH.below < s32.cellMinH.below);
    assert.ok(s16.cellMinH.icon < s16.cellMinH.below);
    assert.equal(s16.cellMinW.icon, 26);
    assert.equal(s16.cellMinW.below, gridCellW());
    assert.equal(s16.rowGap, 4);
    assert.equal(s16.labelGap, 4);
    assert.ok(s16.labelGap >= 2);
    assert.ok(s16.labelGap < s24.labelGap);
    assert.ok(s16.cellMinW.icon < s16.cellMinW.below);
    assert.ok(s16.cellMinW.below < s24.cellMinW.below);
  });

  it('css vars have no cell max-width (cells stretch to columns)', () => {
    const css = metricsCssVars(gridMetrics(16));
    assert.equal(css.includes('cell-max'), false);
    assert.ok(css.includes('--sg-cell-min-below'));
    assert.ok(css.includes('--sg-cell-min-w'));
    assert.ok(css.includes('--sg-label-gap'));
  });
});
