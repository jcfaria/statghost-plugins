/** Statement bounds — port of cuda_statghost/statement.py (pure logic, no vscode API). */

const END_OP = /(\(|,|\+|!|\$|\^|&|\*|-|=|:|~|\||\/|\?|<|>|%[^%]*%)$/;

export function cleanLine(text: string): string {
  if (!text) {
    return '';
  }
  const out: string[] = [];
  let quote: string | null = null;
  let prev = '';
  for (const c of text) {
    if (c === '"' || c === "'" || c === '`') {
      if (quote === null) {
        quote = c;
      } else if (quote === c && prev !== '\\') {
        quote = null;
      }
    }
    if (c === '#' && quote === null) {
      break;
    }
    out.push(c);
    prev = c;
  }
  return out.join('').replace(/\s+$/, '');
}

export function endsInOperator(text: string): boolean {
  const raw = (text || '').trim();
  if (raw === '' || raw.startsWith('#')) {
    return false;
  }
  const s = cleanLine(text);
  if (s.trim() === '') {
    return false;
  }
  if (pySuiteKind(text) === 'owner' || pySuiteKind(text) === 'cont') {
    return false;
  }
  return END_OP.test(s);
}

function newlineInsideString(text: string): boolean {
  let quote: string | null = null;
  let prev = '';
  for (const c of text || '') {
    if (c === '"' || c === "'" || c === '`') {
      if (quote === null) {
        quote = c;
      } else if (quote === c && prev !== '\\') {
        quote = null;
      }
    }
    if (c === '\n' && quote !== null) {
      return true;
    }
    prev = c;
  }
  return false;
}

function hasCodeComment(text: string): boolean {
  const raw = text || '';
  const cleaned = cleanLine(raw);
  return cleaned.length < raw.trimEnd().length;
}

function callDepth(text: string): number {
  let depth = 0;
  let quote: string | null = null;
  let prev = '';
  for (const c of text || '') {
    if (quote) {
      if (c === quote && prev !== '\\') {
        quote = null;
      }
    } else if (c === '"' || c === "'" || c === '`') {
      quote = c;
    } else if (c === '(' || c === '[') {
      depth += 1;
    } else if (c === ')' || c === ']') {
      depth -= 1;
    }
    prev = c;
  }
  return depth;
}

function isCallContinuer(text: string): boolean {
  const s = (text || '').trimStart();
  if (!s) {
    return false;
  }
  return s[0] === ')' || s[0] === ']' || s[0] === ',';
}

export function collapseWraps(text: string | null): string {
  if (text === null || !text.includes('\n')) {
    return text ?? '';
  }
  const raw = text.replace(/\r\n/g, '\n').replace(/\r/g, '\n');
  if (newlineInsideString(raw)) {
    return text;
  }
  const lines = raw.split('\n');
  const out = [lines[0].replace(/\s+$/, '')];
  for (let li = 1; li < lines.length; li++) {
    const line = lines[li];
    const prev = out[out.length - 1];
    const nxt = line.trim();
    if (nxt === '' || nxt.startsWith('#')) {
      out.push(line);
      continue;
    }
    let join = false;
    if (prev && !hasCodeComment(prev)) {
      if (endsInOperator(prev)) {
        join = true;
      } else if (callDepth(prev) > 0 && isCallContinuer(nxt)) {
        join = true;
      }
    }
    if (join) {
      out[out.length - 1] = `${prev} ${nxt}`;
    } else {
      out.push(line.replace(/\s+$/, ''));
    }
  }
  return out.join('\n');
}

function isQuote(c: string): boolean {
  return c === '"' || c === "'" || c === '`';
}

function isOpen(c: string): boolean {
  return c === '(' || c === '[' || c === '{';
}

function isClose(c: string): boolean {
  return c === ')' || c === ']' || c === '}';
}

function bracketsMatch(a: string, b: string): boolean {
  const map: Record<string, string> = {
    ')': '(', ']': '[', '}': '{', '(': ')', '[': ']', '{': '}',
  };
  return map[a] === b;
}

class Pos {
  constructor(
    public line: number,
    public col: number,
  ) {}
}

function charAt(s: string, col: number): string {
  if (col < 0 || col >= s.length) {
    return '';
  }
  return s[col];
}

function nextChar(
  p: Pos,
  lookingForward: boolean,
  getLine: (i: number) => string,
  endsOp: (i: number) => boolean,
  lineCount: number,
): [string, Pos, boolean, boolean] {
  const s = getLine(p.line);
  let isEof = false;
  let isEol = false;
  let nxt: Pos;
  if (lookingForward) {
    if (p.col !== s.length) {
      nxt = new Pos(p.line, p.col + 1);
    } else if (p.line < lineCount - 1) {
      nxt = new Pos(p.line + 1, -1);
    } else {
      isEof = true;
      nxt = new Pos(p.line, p.col);
    }
    const ns = getLine(nxt.line);
    if (nxt.col === ns.length) {
      if (nxt.line === lineCount - 1 || !endsOp(nxt.line)) {
        isEol = true;
      }
    }
  } else if (p.col !== -1) {
    nxt = new Pos(p.line, p.col - 1);
  } else if (p.line > 0) {
    nxt = new Pos(p.line - 1, getLine(p.line - 1).length - 1);
  } else {
    isEof = true;
    nxt = new Pos(p.line, p.col);
  }
  if (!lookingForward && nxt.col === -1) {
    if (nxt.line <= 0 || !endsOp(nxt.line - 1)) {
      isEol = true;
    }
  }
  const ch = charAt(getLine(nxt.line), nxt.col);
  return [ch, nxt, isEol, isEof];
}

function remainderAfterControlHeader(s: string): string | null {
  const t = (s || '').trim();
  if (!t) {
    return null;
  }
  if (/^else\s+if\b/i.test(t)) {
    // fall through
  } else if (/^(else|repeat)\b/i.test(t)) {
    const m = /^(?:else|repeat)\b(.*)$/i.exec(t);
    return (m?.[1] ?? '').trim();
  }
  const m = /^(?:else\s+)?(?:if|for|while)\b\s*/i.exec(t);
  if (!m) {
    return null;
  }
  const rest = t.slice(m[0].length);
  if (!rest.startsWith('(')) {
    return null;
  }
  let depth = 0;
  let quote = '';
  let prev = '';
  for (let i = 0; i < rest.length; i++) {
    const c = rest[i];
    if (quote) {
      if (c === quote && prev !== '\\') {
        quote = '';
      }
    } else if (c === '"' || c === "'" || c === '`') {
      quote = c;
    } else if (c === '(') {
      depth += 1;
    } else if (c === ')') {
      depth -= 1;
      if (depth === 0) {
        return rest.slice(i + 1).trim();
      }
    }
    prev = c;
  }
  return null;
}

function joinedCode(getLine: (i: number) => string, start: number, end: number): string {
  const parts: string[] = [];
  for (let i = start; i <= end; i++) {
    parts.push(cleanLine(getLine(i) ?? ''));
  }
  return parts.join(' ').trim();
}

function controlNeedsBody(getLine: (i: number) => string, start: number, end: number): boolean {
  return remainderAfterControlHeader(joinedCode(getLine, start, end)) === '';
}

function nextCodeLine(i: number, getLine: (n: number) => string, lineCount: number): number | null {
  let j = i + 1;
  while (j < lineCount) {
    const t = getLine(j);
    const s = (t ?? '').trim();
    if (s === '') {
      return null;
    }
    if (s.startsWith('#')) {
      j += 1;
      continue;
    }
    return j;
  }
  return null;
}

function growRControl(
  start: number,
  end: number,
  getLine: (i: number) => string,
  lineCount: number,
  depth = 0,
): [number, number] {
  if (depth > 32) {
    return [start, end];
  }
  let grown = true;
  let e = end;
  while (grown) {
    grown = false;
    if (controlNeedsBody(getLine, start, e)) {
      const nxt = nextCodeLine(e, getLine, lineCount);
      if (nxt !== null) {
        let [, b1] = extendBrackets(nxt, getLine, lineCount);
        [, b1] = growRControl(nxt, b1, getLine, lineCount, depth + 1);
        if (b1 > e) {
          e = b1;
          grown = true;
          continue;
        }
      }
    }
    const nxt = nextCodeLine(e, getLine, lineCount);
    if (nxt === null) {
      break;
    }
    const head = cleanLine(getLine(nxt) ?? '').trim();
    if (/^else\b/i.test(head)) {
      const head0 = cleanLine(getLine(start) ?? '').trim();
      if (!/^(?:else\s+)?(?:if|for|while|repeat)\b/i.test(head0)) {
        break;
      }
      let [, e1] = extendBrackets(nxt, getLine, lineCount);
      [, e1] = growRControl(nxt, e1, getLine, lineCount, depth + 1);
      if (e1 > e) {
        e = e1;
        grown = true;
      }
    }
  }
  return [start, e];
}

function extendBrackets(
  line: number,
  getLine: (i: number) => string,
  lineCount: number,
): [number, number] {
  if (lineCount <= 0) {
    return [0, 0];
  }
  let ln = line;
  if (ln < 0) {
    ln = 0;
  }
  if (ln >= lineCount) {
    ln = lineCount - 1;
  }

  const lineAt = (i: number) => getLine(i) ?? '';
  const endsOp = (i: number) => endsInOperator(lineAt(i));

  let lookingForward = true;
  const poss: Pos[] = [new Pos(ln, 0), new Pos(ln, -1)];
  const done = [false, false];
  const unmatched: string[][] = [[], []];
  let abort = false;
  let quote = '';
  let prev = '';

  while (!abort && !(done[0] && done[1])) {
    const d = lookingForward ? 1 : 0;
    const [ch, nxt, isEol, isEof] = nextChar(poss[d], lookingForward, lineAt, endsOp, lineCount);
    poss[d] = nxt;
    if (quote === '') {
      if (isQuote(ch)) {
        quote = ch;
      } else if (lookingForward ? isOpen(ch) : isClose(ch)) {
        unmatched[d].push(ch);
      } else if (lookingForward ? isClose(ch) : isOpen(ch)) {
        if (unmatched[d].length === 0) {
          lookingForward = !lookingForward;
          const d2 = lookingForward ? 1 : 0;
          unmatched[d2].push(ch);
          done[d2] = false;
        } else if (!bracketsMatch(ch, unmatched[d].pop()!)) {
          abort = true;
        }
      }
    } else if (ch === quote) {
      if (lookingForward) {
        if (prev !== '\\') {
          quote = '';
        }
      } else {
        const [nch] = nextChar(poss[d], lookingForward, lineAt, endsOp, lineCount);
        if (nch !== '\\') {
          quote = '';
        }
      }
    }
    if (isEol) {
      if (quote !== '') {
        if (isEof) {
          abort = true;
        }
      } else if (unmatched[lookingForward ? 1 : 0].length === 0) {
        done[lookingForward ? 1 : 0] = true;
        lookingForward = !lookingForward;
      } else if (isEof) {
        abort = true;
      }
    }
    prev = ch;
  }
  if (abort) {
    return [ln, ln];
  }
  return [poss[0].line, poss[1].line];
}

function openerIfInsideString(line: number, getLine: (i: number) => string): number {
  let start = line;
  while (start > 0) {
    const s = (getLine(start - 1) ?? '').trim();
    if (s === '' || s.startsWith('#')) {
      break;
    }
    start -= 1;
  }
  let quote = '';
  let opener: number | null = null;
  for (let i = start; i < line; i++) {
    let prev = '';
    for (const c of getLine(i) ?? '') {
      if (quote) {
        if (c === quote && prev !== '\\') {
          quote = '';
          opener = null;
        }
      } else if (c === '"' || c === "'" || c === '`') {
        quote = c;
        opener = i;
      }
      prev = c;
    }
  }
  if (quote && opener !== null) {
    return opener;
  }
  return line;
}

export function extendStatement(
  line: number,
  getLine: (i: number) => string,
  lineCount: number,
): [number, number] {
  const opener = openerIfInsideString(line, getLine);
  let [start, end] = extendBrackets(opener, getLine, lineCount);
  [start, end] = growRControl(start, end, getLine, lineCount);
  return growPyCompound(start, end, getLine, lineCount);
}

const RE_R_FUN_HEAD = /^\s*(?:[.`\w]+|`[^`]+`)\s*(?:<-|=)\s*function\s*\(/;
const RE_PY_DEF = /^(\s*)(?:async\s+)?(?:def|class)\s+[A-Za-z_]\w*\s*[(:]/;
const RE_JL_FUN = /^\s*(?:function|macro)\s+[A-Za-z_!][\w!]*/;
const RE_PY_OWNER = /^(?:async\s+)?(?:def|class|if|for|while|try|with|match)\b/;
const RE_PY_CONTINUER = /^(?:elif|else|except|finally|case)\b/;

function pySuiteKind(line: string): 'owner' | 'cont' | 'deco' | null {
  const s = cleanLine(line).trim();
  if (!s) {
    return null;
  }
  if (s.startsWith('@') && !s.startsWith('@"') && !s.startsWith("@'")) {
    return 'deco';
  }
  if (!s.endsWith(':')) {
    return null;
  }
  if (RE_PY_OWNER.test(s)) {
    return 'owner';
  }
  if (RE_PY_CONTINUER.test(s)) {
    return 'cont';
  }
  return null;
}

function includeDecorators(start: number, getLine: (i: number) => string): number {
  let i = start;
  while (i > 0) {
    if (pySuiteKind(getLine(i - 1)) === 'deco') {
      i -= 1;
      continue;
    }
    break;
  }
  return i;
}

function pyFindOwner(line: number, getLine: (i: number) => string): number | null {
  const myInd = indentWidth(getLine(line));
  for (let j = line - 1; j >= 0; j--) {
    const raw = getLine(j);
    const s = (raw ?? '').trim();
    if (s === '') {
      return null;
    }
    if (s.startsWith('#')) {
      continue;
    }
    const ind = indentWidth(raw);
    if (ind > myInd) {
      continue;
    }
    if (ind < myInd) {
      return null;
    }
    const kind = pySuiteKind(raw);
    if (kind === 'owner') {
      return j;
    }
    if (kind === 'cont') {
      continue;
    }
    return null;
  }
  return null;
}

function pyExtendSuite(start: number, getLine: (i: number) => string, lineCount: number): number {
  let i = start;
  while (i < lineCount && pySuiteKind(getLine(i)) === 'deco') {
    i += 1;
  }
  if (i >= lineCount) {
    return start;
  }
  const kind = pySuiteKind(getLine(i));
  if (kind !== 'owner' && kind !== 'cont') {
    return i > start ? i - 1 : start;
  }
  const headInd = indentWidth(getLine(i));
  let end = i;
  let j = i + 1;
  while (j < lineCount) {
    const raw = getLine(j) ?? '';
    const s = raw.trim();
    if (s === '') {
      return end;
    }
    if (s.startsWith('#')) {
      j += 1;
      continue;
    }
    const ind = indentWidth(raw);
    const nxt = pySuiteKind(raw);
    if (ind > headInd) {
      end = j;
      j += 1;
      continue;
    }
    if (ind === headInd && nxt === 'cont') {
      end = j;
      j += 1;
      continue;
    }
    break;
  }
  return end;
}

function growPyCompound(
  start: number,
  end: number,
  getLine: (i: number) => string,
  lineCount: number,
): [number, number] {
  const kind = pySuiteKind(getLine(start));
  if (kind === null) {
    return [start, end];
  }
  let i = start;
  if (kind === 'cont') {
    const owner = pyFindOwner(i, getLine);
    if (owner !== null) {
      i = owner;
    }
  }
  i = includeDecorators(i, getLine);
  let newEnd = pyExtendSuite(i, getLine, lineCount);
  if (newEnd < end) {
    newEnd = end;
  }
  return [i, newEnd];
}

export function dedentBlock(text: string | null): string {
  if (text === null) {
    return '';
  }
  const raw = text.replace(/\r\n/g, '\n').replace(/\r/g, '\n');
  if (raw.trim() === '') {
    return raw;
  }
  const lines = raw.split('\n');
  const margin = minMargin(lines);
  if (margin <= 0) {
    return raw;
  }
  return lines.map((ln) => (ln.trim() === '' ? ln : ln.slice(margin))).join('\n');
}

function minMargin(lines: string[]): number {
  let m = Number.POSITIVE_INFINITY;
  for (const ln of lines) {
    if (ln.trim() === '') {
      continue;
    }
    const lead = ln.length - ln.trimStart().length;
    if (lead < m) {
      m = lead;
    }
  }
  return m === Number.POSITIVE_INFINITY ? 0 : m;
}

function indentWidth(line: string): number {
  let n = 0;
  for (const c of line || '') {
    if (c === ' ') {
      n += 1;
    } else if (c === '\t') {
      n += 4;
    } else {
      break;
    }
  }
  return n;
}

function isBlankOrComment(line: string): boolean {
  const s = (line || '').trim();
  return s === '' || s.startsWith('#');
}

export function enclosingFunction(
  line: number | null,
  getLine: (i: number) => string,
  lineCount: number | null,
): [number | null, number | null] {
  if (line === null || lineCount === null || lineCount <= 0) {
    return [null, null];
  }
  let ln = Math.trunc(line);
  if (ln < 0) {
    ln = 0;
  }
  if (ln >= lineCount) {
    ln = lineCount - 1;
  }

  const lineAt = (i: number) => getLine(i) ?? '';

  for (let i = ln; i >= 0; i--) {
    const raw = lineAt(i);
    if (!RE_R_FUN_HEAD.test(raw)) {
      continue;
    }
    const [s, e] = extendStatement(i, getLine, lineCount);
    if (s <= ln && ln <= e) {
      return [s, e];
    }
  }

  const caretRaw = lineAt(ln);
  let caretInd = indentWidth(caretRaw);
  let searchFrom = ln;
  if (pySuiteKind(caretRaw) === 'deco') {
    let j = ln + 1;
    while (j < lineCount && (pySuiteKind(lineAt(j)) === 'deco' || isBlankOrComment(lineAt(j)))) {
      j += 1;
    }
    if (j < lineCount && RE_PY_DEF.test(lineAt(j))) {
      searchFrom = j;
      caretInd = indentWidth(lineAt(j));
    }
  }
  if (isBlankOrComment(caretRaw) && pySuiteKind(caretRaw) !== 'deco') {
    let found = false;
    for (let j = ln + 1; j < lineCount; j++) {
      if (!isBlankOrComment(lineAt(j))) {
        caretInd = indentWidth(lineAt(j));
        found = true;
        break;
      }
    }
    if (!found) {
      for (let j = ln - 1; j >= 0; j--) {
        if (!isBlankOrComment(lineAt(j))) {
          caretInd = indentWidth(lineAt(j));
          break;
        }
      }
    }
  }
  for (let i = searchFrom; i >= 0; i--) {
    const raw = lineAt(i);
    if (!RE_PY_DEF.test(raw)) {
      continue;
    }
    const headInd = indentWidth(raw);
    if (headInd > caretInd) {
      continue;
    }
    let end = i;
    for (let j = i + 1; j < lineCount; j++) {
      const lj = lineAt(j);
      if (isBlankOrComment(lj)) {
        continue;
      }
      if (indentWidth(lj) > headInd) {
        end = j;
        continue;
      }
      break;
    }
    const deco = includeDecorators(i, lineAt);
    if (deco <= ln && ln <= end) {
      return [deco, end];
    }
  }

  for (let i = ln; i >= 0; i--) {
    const raw = lineAt(i);
    if (!RE_JL_FUN.test(raw)) {
      continue;
    }
    let depth = 1;
    let end = i;
    for (let j = i + 1; j < lineCount; j++) {
      const lj = lineAt(j).trim();
      if (/^(?:function|macro|struct|mutable\s+struct|for|while|if|let|quote|begin)\b/.test(lj)) {
        depth += 1;
      }
      if (/^end\b/.test(lj)) {
        depth -= 1;
        if (depth === 0) {
          end = j;
          break;
        }
      }
      end = j;
    }
    if (i <= ln && ln <= end && depth === 0) {
      return [i, end];
    }
  }

  return [null, null];
}

export function joinLines(getLine: (i: number) => string, start: number, end: number): string {
  const parts: string[] = [];
  for (let i = start; i <= end; i++) {
    parts.push(getLine(i) ?? '');
  }
  return parts.join('\n');
}

export function statementAtCaret(
  caretLine: number | undefined,
  getLine: (i: number) => string,
  lineCount: number,
): { start: number | null; end: number | null; text: string; mode: string } {
  if (caretLine === undefined) {
    return { start: null, end: null, text: '', mode: 'statement' };
  }
  const [fs, fe] = enclosingFunction(caretLine, getLine, lineCount);
  if (fs !== null && fe !== null) {
    return {
      start: fs,
      end: fe,
      text: dedentBlock(joinLines(getLine, fs, fe)),
      mode: 'function',
    };
  }
  let y = caretLine;
  while (y < lineCount && isBlankOrComment(getLine(y))) {
    y += 1;
  }
  if (y >= lineCount) {
    return { start: null, end: null, text: '', mode: 'statement' };
  }
  const [start, end] = extendStatement(y, getLine, lineCount);
  return {
    start,
    end,
    text: dedentBlock(joinLines(getLine, start, end)),
    mode: 'statement',
  };
}
