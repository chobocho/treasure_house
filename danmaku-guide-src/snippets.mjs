import { readFileSync, realpathSync } from 'node:fs';
import { resolve, sep } from 'node:path';

// 바깥 영역에도 안쪽 본문을 보존한다. 문자 수 n, 최대 중첩 d일 때 시간·추가 공간 O(n*d).
export function extractRegion(source, name) {
  const lines = source.replace(/\r\n/g, '\n').split('\n');
  const stack = [];
  const found = new Map();
  for (const line of lines) {
    const start = line.match(/^\s*(?:#|\/\/)\s*(?:#)?region\s+([a-z0-9]+(?:-[a-z0-9]+)*)\s*$/);
    if (start) {
      if (found.has(start[1]) || stack.some((s) => s.name === start[1])) throw new Error(`중복 영역: ${start[1]}`);
      stack.push({ name: start[1], lines: [] });
      continue;
    }
    if (/^\s*(?:#|\/\/)\s*(?:#)?endregion\s*$/.test(line)) {
      if (!stack.length) throw new Error('열리지 않은 영역의 종료 표식');
      const region = stack.pop();
      found.set(region.name, region.lines);
      if (stack.length) stack.at(-1).lines.push(...region.lines);
      continue;
    }
    if (stack.length) stack.at(-1).lines.push(line);
  }
  if (stack.length) throw new Error(`닫히지 않은 영역: ${stack.at(-1).name}`);
  if (!found.has(name)) throw new Error(`영역을 찾을 수 없다: ${name}`);
  return dedent(found.get(name).join('\n'));
}

export function dedent(source) {
  const lines = source.replace(/\r\n/g, '\n').replace(/[ \t\n]+$/, '').split('\n');
  while (lines.length && !lines[0].trim()) lines.shift();
  const widths = lines.filter((line) => line.trim()).map((line) => line.match(/^\s*/)[0].length);
  const width = Math.min(...widths);
  return lines.map((line) => line.slice(width).replace(/[ \t]+$/, '')).join('\n');
}

export function renderSnippet(source, { limit = true } = {}) {
  const value = dedent(source);
  if (limit && value.split('\n').length > 30) throw new Error('코드 영역이 30줄을 넘는다');
  return value.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

export function resolveSnippet(root, reference, options) {
  const [path, region] = reference.split('#');
  if (!path || reference.split('#').length > 2) throw new Error(`잘못된 코드 출처: ${reference}`);
  const target = resolve(root, path);
  if (!target.startsWith(resolve(root) + sep)) throw new Error(`소스 경로가 범위를 벗어난다: ${reference}`);
  if (!realpathSync(target).startsWith(realpathSync(root) + sep)) throw new Error(`소스 링크가 범위를 벗어난다: ${reference}`);
  const source = readFileSync(target, 'utf8');
  const value = region ? extractRegion(source, region) : source.replace(/^\s*(?:#|\/\/)\s*#?(?:end)?region\b[^\n]*(?:\n|$)/gm, '');
  return renderSnippet(value, options);
}
