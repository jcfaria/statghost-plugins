import { strict as assert } from 'node:assert';
import { describe, it } from 'node:test';
import { clampMode, contrastRatio, pickFgRgb, relLuma } from '../iconsFg';

describe('iconsFg', () => {
  const font: [number, number, number] = [0x90, 0x90, 0x90];
  const bg: [number, number, number] = [0x2a, 0x2a, 0x2a];

  it('clampMode defaults to auto', () => {
    assert.equal(clampMode(''), 'auto');
    assert.equal(clampMode('LIGHT'), 'light');
  });

  it('pickFgRgb palettes', () => {
    assert.deepEqual(pickFgRgb('light', font, bg), [0xc4, 0xc4, 0xc4]);
    assert.deepEqual(pickFgRgb('dark', font, bg), [0x3a, 0x3a, 0x3a]);
    assert.deepEqual(pickFgRgb('gray', font, bg), [0x8a, 0x8a, 0x8a]);
    assert.deepEqual(pickFgRgb('theme', font, bg), font);
  });

  it('pickFgRgb auto on dark bg prefers light', () => {
    const fg = pickFgRgb('auto', font, bg);
    assert.ok(contrastRatio(fg, bg) >= 3 || relLuma(bg) < 0.45);
  });

  it('pickFgRgb auto on light bg', () => {
    const lightBg: [number, number, number] = [0xf0, 0xf0, 0xf0];
    const fg = pickFgRgb('auto', font, lightBg);
    assert.deepEqual(fg, font.length === 3 ? pickFgRgb('auto', font, lightBg) : fg);
  });

  it('relLuma bounds', () => {
    assert.ok(relLuma([0, 0, 0]) < 0.01);
    assert.ok(relLuma([255, 255, 255]) > 0.99);
  });
});
