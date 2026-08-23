import { strict as assert } from 'node:assert';
import { describe, it } from 'node:test';
import {
  CMD_ARM,
  CMD_EVAL,
  CMD_EVAL_KEEP,
  makeCommand,
  makeEval,
  nextArmCmd,
  parseMessage,
  PREFIX,
} from '../protocol';

describe('protocol', () => {
  it('makeCommand prefix and nonce', () => {
    const a = makeCommand('ARM');
    const b = makeCommand('ARM');
    assert.ok(a.startsWith(PREFIX + 'ARM '));
    assert.notEqual(a, b);
  });

  it('makeEval body', () => {
    const msg = makeEval('x <- 1', false);
    assert.ok(msg.startsWith(PREFIX + CMD_EVAL + ' '));
    assert.ok(msg.endsWith('\nx <- 1'));
    const keep = makeEval('y', true);
    assert.ok(keep.includes(CMD_EVAL_KEEP));
  });

  it('parseMessage round trip', () => {
    const raw = makeEval('print(1)');
    const { cmd, body } = parseMessage(raw);
    assert.equal(cmd, CMD_EVAL);
    assert.equal(body, 'print(1)');
  });

  it('parseMessage rejects junk', () => {
    assert.deepEqual(parseMessage('hello'), { cmd: null, body: null });
  });

  it('nextArmCmd absolute', () => {
    assert.equal(nextArmCmd(false), CMD_ARM);
    assert.equal(nextArmCmd(true), 'IDLE');
  });
});
