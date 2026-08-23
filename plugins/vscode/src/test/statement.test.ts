import { strict as assert } from 'node:assert';
import { describe, it } from 'node:test';
import {
  dedentBlock,
  extendStatement,
  joinLines,
  statementAtCaret,
} from '../statement';

function lines(src: string): string[] {
  return src.replace(/\r\n/g, '\n').replace(/\r/g, '\n').split('\n');
}

function get(rows: string[]): (i: number) => string {
  return (i) => rows[i] ?? '';
}

function span(src: string, y: number): [number, number, string] {
  const rows = lines(src);
  const [s, e] = extendStatement(y, get(rows), rows.length);
  return [s, e, dedentBlock(joinLines(get(rows), s, e))];
}

describe('statement', () => {
  it('r wrapped call', () => {
    const src = 'rnorm(n = 1e2,\n      mean = 10,\n      sd = 2)\n';
    const [s, e, text] = span(src, 0);
    assert.deepEqual([s, e], [0, 2]);
    assert.ok(text.includes('sd = 2)'));
  });

  it('r unbraced if', () => {
    const src = (
      'if (!requireNamespace("magrittr", quietly = TRUE))\n'
      + '  install.packages("magrittr")\n'
      + 'library(magrittr)\n'
    );
    const [s, e, text] = span(src, 0);
    assert.equal(s, 0);
    assert.equal(e, 1);
    assert.ok(text.includes('install.packages'));
    assert.ok(!text.includes('library'));
  });

  it('statementAtCaret advances from comment line', () => {
    const rows = lines('# comment\nx <- 1\n');
    const out = statementAtCaret(0, get(rows), rows.length);
    assert.equal(out.text.trim(), 'x <- 1');
    assert.equal(out.end, 1);
  });

  it('dedent method block', () => {
    const src = '    def dist2(self):\n        return self.x\n';
    const out = dedentBlock(src);
    assert.ok(out.startsWith('def dist2'));
  });
});
