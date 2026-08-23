import { strict as assert } from 'node:assert';
import { describe, it } from 'node:test';
import {
  ACTION_KEYS,
  collapseKeys,
  collapseNestedRows,
  DEFAULT_SHOW,
  formatShow,
  gridKeys,
  gridPlan,
  GRID_COLS,
  GRID_GROUP_TITLES,
  GRID_CAP,
  GRID_CAP_SLACK,
  GRID_CELL_MIN,
  GRID_EMU_CHAR,
  gridCellW,
  GRID_GROUPS,
  GRID_LABEL_DEFAULT,
  menuPath,
  parseGridLabel,
  parseShow,
  nestMenuKeys,
  filterToolbarRows,
} from '../chromeContract';

describe('chromeContract', () => {
  it('parseShow empty → DEFAULT_SHOW', () => {
    assert.deepEqual(parseShow(''), [...DEFAULT_SHOW]);
  });

  it('parseShow filters and orders canonically', () => {
    assert.deepEqual(parseShow('clear,cfg,send'), ['cfg', 'send', 'clear']);
  });

  it('collapseKeys hides nest children when parent present', () => {
    const out = collapseKeys(['send', 'function', 'clear', 'close_graphics']);
    assert.ok(out.includes('send'));
    assert.ok(!out.includes('function'));
    assert.ok(out.includes('clear'));
    assert.ok(!out.includes('close_graphics'));
  });

  it('gridPlan all actions three cols', () => {
    const plan = gridPlan();
    const hdrs: string[] = [];
    const keys: string[] = [];
    for (const entry of plan) {
      if (entry[0] === 'hdr') {
        hdrs.push(entry[1]);
      } else {
        assert.ok(entry[1].length <= GRID_COLS);
        keys.push(...entry[1]);
      }
    }
    assert.deepEqual(keys, [...ACTION_KEYS]);
    assert.deepEqual(hdrs, [...GRID_GROUP_TITLES]);
  });

  it('gridPlan filters empty groups', () => {
    const plan = gridPlan(['send', 'function', 'clear']);
    const hdrs = plan.filter((e) => e[0] === 'hdr').map((e) => e[1]);
    assert.deepEqual(hdrs, ['Send', 'Clear']);
  });

  it('gridKeys equals ACTION_KEYS', () => {
    assert.deepEqual(gridKeys(), ACTION_KEYS);
  });

  it('parseGridLabel aliases', () => {
    assert.equal(parseGridLabel(''), GRID_LABEL_DEFAULT);
    assert.equal(parseGridLabel('under'), 'below');
    assert.equal(parseGridLabel('icons'), 'icon');
    assert.equal(parseGridLabel('horz'), 'icon');
    assert.equal(parseGridLabel('junk'), 'below');
  });

  it('GRID_CAP covers all keys', () => {
    assert.deepEqual(new Set(Object.keys(GRID_CAP)), new Set(ACTION_KEYS));
  });

  it('GRID_GROUPS flatten to ACTION_KEYS', () => {
    const flat = GRID_GROUPS.flat();
    assert.deepEqual(flat, [...ACTION_KEYS]);
  });

  it('gridCellW is longest caption + 20%', () => {
    const longest = Math.max(...Object.values(GRID_CAP).map((c) => c.length));
    const expect = Math.max(
      GRID_CELL_MIN,
      Math.round(longest * GRID_EMU_CHAR * GRID_CAP_SLACK),
    );
    assert.equal(gridCellW(), expect);
    assert.ok(gridCellW(['Sel', 'VeryLongCaption']) > gridCellW(['Sel', 'Source']));
  });

  it('menuPath nest captions', () => {
    assert.equal(menuPath('cfg'), 'Config');
    assert.equal(menuPath('send'), 'Send\\Send');
    assert.equal(menuPath('function'), 'Send\\Function');
    assert.equal(menuPath('inspect'), 'Inspect\\Print');
    assert.equal(menuPath('clear_all'), 'Clear\\Clear all');
  });

  it('nestMenuKeys', () => {
    assert.deepEqual(
      nestMenuKeys('send', [...DEFAULT_SHOW]),
      ['function', 'above', 'below', 'chunk'],
    );
    assert.deepEqual(nestMenuKeys('cfg', [...DEFAULT_SHOW]), []);
  });

  it('collapseNestedRows on toolbar', () => {
    const tb = [
      ['send', 'h', 'send_selection', 'send.png'],
      ['function', 'h', 'send_function', 'function.png'],
      ['clear', 'h', 'clear_console', 'clear.png'],
    ] as const;
    const rows = filterToolbarRows(tb, [...DEFAULT_SHOW]);
    const names = collapseNestedRows(rows).map((r) => r[0]);
    assert.ok(names.includes('send'));
    assert.ok(!names.includes('function'));
  });

  it('formatShow canonical order', () => {
    assert.equal(formatShow(['clear', 'cfg']), 'cfg,clear');
  });
});
