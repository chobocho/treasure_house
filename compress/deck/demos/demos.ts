// 덱 안에서 도는 데모들 — TypeScript 로 쓰고 deck/demos.js 로 옮긴다.
//
//   make demos     # tsc 로 옮긴다 (deck/demos.js 를 새로 쓴다)
//
// 규칙 셋.
//   · 바깥 의존이 없다. 덱은 파일 하나로 열려야 한다.
//   · 본문 모듈(src/)을 부르지 않는다 — 브라우저에 가져올 수 없다.
//     대신 **같은 알고리즘을 같은 규칙으로** 다시 적고, check_deck.js 의
//     CASES 가 기댓값을 못 박는다.
//   · 화면에 그리는 것은 api.w 하나뿐이다. 그래야 검사기가 무엇이
//     그려졌는지 알 수 있다.
interface Api {
  w(host: any, html: string, cls?: string): void;
  esc(s: string): string;
  show(v: unknown): string;
  num(n: number): string;
}

type Demo = (host: any, api: Api) => void;

declare function __demo(id: string, fn: Demo): void;

// 입력칸을 찾아 값을 읽는다. 없으면 기본값.
// 입력칸은 data-<이름> 으로 표시한다. check_deck.js 의 DOM 스텁이
// 그 모양을 보고 값을 넣어 주므로, 검사기가 데모를 실제로 몰아 볼 수
// 있다 — 모양을 바꾸면 검사가 조용히 기본값만 보게 된다.
function val(host: any, name: string, dflt: string): string {
  const el = host.querySelector('[data-' + name + ']');
  const v = el && el.value;
  return (v === undefined || v === null || v === '') ? dflt : String(v);
}

function bytesOf(text: string): number[] {
  const out: number[] = [];
  for (const ch of text) {
    const c = ch.codePointAt(0) as number;
    if (c < 0x80) {
      out.push(c);
    } else if (c < 0x800) {
      out.push(0xc0 | (c >> 6), 0x80 | (c & 63));
    } else if (c < 0x10000) {
      out.push(0xe0 | (c >> 12), 0x80 | ((c >> 6) & 63), 0x80 | (c & 63));
    } else {
      out.push(0xf0 | (c >> 18), 0x80 | ((c >> 12) & 63),
               0x80 | ((c >> 6) & 63), 0x80 | (c & 63));
    }
  }
  return out;
}

function hex(b: number): string {
  return b.toString(16).toUpperCase().padStart(2, '0');
}

function bind(host: any, run: () => void): void {
  const go = host.querySelector('button');
  if (go) go.addEventListener('click', run);
  const ins = host.querySelectorAll('input');
  for (let i = 0; i < ins.length; i++) {
    ins[i].addEventListener('input', run);
  }
  run();
}

// ── 1부 · 엔트로피 ────────────────────────────────────────────────
__demo('entropy', (host, api) => {
  const run = () => {
    const text = val(host, 'text', 'abracadabra');
    const data = bytesOf(text);
    if (!data.length) {
      api.w(host, '글자를 넣어 보세요', 'dim');
      return;
    }
    const count: Record<number, number> = {};
    for (const b of data) count[b] = (count[b] || 0) + 1;
    let h = 0;
    const rows: string[] = [];
    const keys = Object.keys(count).map(Number).sort((a, b) => a - b);
    for (const k of keys) {
      const p = count[k] / data.length;
      h -= p * Math.log2(p);
    }
    for (const k of keys.slice(0, 8)) {
      const p = count[k] / data.length;
      rows.push('  ' + api.esc(String.fromCharCode(k)) + '  ' + count[k]
        + '회  p=' + p.toFixed(3) + '  ' + (-Math.log2(p)).toFixed(2) + '비트');
    }
    const need = Math.ceil(data.length * h / 8);
    api.w(host,
      '바이트 ' + data.length + '개 · 서로 다른 값 ' + keys.length + '가지\n'
      + rows.join('\n') + (keys.length > 8 ? '\n  …' : '') + '\n'
      + '\n0차 엔트로피  <span class="ok">' + h.toFixed(4) + ' 비트/바이트</span>'
      + '\n이론상 최소  <span class="ok">' + need + ' 바이트</span>'
      + '  (원본 ' + data.length + ' 바이트)');
  };
  bind(host, run);
});

// ── 2부 · varint ──────────────────────────────────────────────────
__demo('varint', (host, api) => {
  const run = () => {
    const raw = val(host, 'n', '300');
    let n = Math.floor(Number(raw));
    if (!isFinite(n) || n < 0) {
      api.w(host, '0 이상의 정수를 넣어 보세요', 'bad');
      return;
    }
    const parts: string[] = [];
    const bytes: number[] = [];
    let v = n;
    do {
      const g = v % 128;
      v = Math.floor(v / 128);
      const more = v > 0;
      bytes.push(more ? (g | 0x80) : g);
      parts.push((more ? '1' : '0') + ' '
        + g.toString(2).padStart(7, '0'));
    } while (v > 0);
    api.w(host,
      '값 ' + n + ' = 0b' + n.toString(2) + '\n\n'
      + parts.map((p, i) => '  바이트 ' + i + '   ' + p
          + '   0x' + hex(bytes[i])).join('\n')
      + '\n\n<span class="ok">' + bytes.length + ' 바이트</span>'
      + '  (고정 4바이트 대비 ' + (4 - bytes.length) + '바이트 절약)');
  };
  bind(host, run);
});

// ── 3부 · PackBits ────────────────────────────────────────────────
__demo('packbits', (host, api) => {
  const run = () => {
    const text = val(host, 'text', 'aaaaabcdeffffff');
    const src = bytesOf(text);
    if (!src.length) {
      api.w(host, '글자를 넣어 보세요', 'dim');
      return;
    }
    const rows: string[] = [];
    let out = 0;
    let i = 0;
    while (i < src.length) {
      let run = 1;
      while (i + run < src.length && src[i + run] === src[i] && run < 128) {
        run++;
      }
      if (run >= 3) {
        rows.push('  런      0x' + hex(257 - run) + '  '
          + api.esc(String.fromCharCode(src[i])) + ' × ' + run
          + '   → 2바이트');
        out += 2;
        i += run;
      } else {
        let j = i;
        let lit = '';
        while (j < src.length && j - i < 128) {
          let r = 1;
          while (j + r < src.length && src[j + r] === src[j]) r++;
          if (r >= 3) break;
          lit += String.fromCharCode(src[j]);
          j += r;
        }
        if (j === i) j = i + 1;
        rows.push('  리터럴  0x' + hex(j - i - 1) + '  '
          + api.esc(lit) + '   → ' + (j - i + 1) + '바이트');
        out += j - i + 1;
        i = j;
      }
    }
    api.w(host, rows.join('\n') + '\n\n원본 ' + src.length
      + ' → <span class="' + (out < src.length ? 'ok' : 'bad') + '">'
      + out + ' 바이트</span>  ('
      + (100 * out / src.length).toFixed(1) + '%)');
  };
  bind(host, run);
});

// ── 3부 · MTF ─────────────────────────────────────────────────────
__demo('mtf', (host, api) => {
  const run = () => {
    const text = val(host, 'text', 'bbaac');
    const src = bytesOf(text).slice(0, 24);
    if (!src.length) {
      api.w(host, '글자를 넣어 보세요', 'dim');
      return;
    }
    const table: number[] = [];
    for (const b of src) if (table.indexOf(b) < 0) table.push(b);
    table.sort((a, b) => a - b);
    const shown = table.slice();
    const rows: string[] = [];
    const outs: number[] = [];
    for (const b of src) {
      const i = table.indexOf(b);
      outs.push(i);
      rows.push('  ' + api.esc(String.fromCharCode(b)) + '  표 '
        + api.esc(table.map((x) => String.fromCharCode(x)).join(''))
        + '  → ' + i);
      table.splice(i, 1);
      table.unshift(b);
    }
    const zeros = outs.filter((x) => x === 0).length;
    api.w(host,
      '표 시작  ' + api.esc(shown.map((x) => String.fromCharCode(x)).join(''))
      + '\n' + rows.join('\n')
      + '\n\n출력  [' + outs.join(', ') + ']'
      + '\n0 의 개수  <span class="ok">' + zeros + '</span> / '
      + outs.length + '  — 0 이 많을수록 뒤의 부호기가 먹기 좋다');
  };
  bind(host, run);
});

// ── 4부 · 캐노니컬 허프만 ─────────────────────────────────────────
__demo('huffman', (host, api) => {
  const run = () => {
    const text = val(host, 'text', 'abracadabra');
    const src = bytesOf(text);
    if (src.length < 2) {
      api.w(host, '두 글자 이상 넣어 보세요', 'dim');
      return;
    }
    const count: Record<number, number> = {};
    for (const b of src) count[b] = (count[b] || 0) + 1;
    const syms = Object.keys(count).map(Number).sort(
      (a, b) => count[a] - count[b] || a - b);
    // 길이만 구한다 — 트리를 만들지 않는 것이 이 덱의 방식이다.
    const lens: Record<number, number> = {};
    if (syms.length === 1) {
      lens[syms[0]] = 1;
    } else {
      type Node = { w: number; syms: number[] };
      let nodes: Node[] = syms.map((s) => ({ w: count[s], syms: [s] }));
      for (const s of syms) lens[s] = 0;
      while (nodes.length > 1) {
        nodes.sort((a, b) => a.w - b.w || a.syms[0] - b.syms[0]);
        const a = nodes.shift() as Node;
        const b = nodes.shift() as Node;
        for (const s of a.syms.concat(b.syms)) lens[s]++;
        nodes.push({ w: a.w + b.w, syms: a.syms.concat(b.syms) });
      }
    }
    // 캐노니컬 배정 — 길이 순, 같은 길이면 기호 순
    const order = syms.slice().sort(
      (a, b) => lens[a] - lens[b] || a - b);
    let code = 0;
    let prev = lens[order[0]];
    const rows: string[] = [];
    let bits = 0;
    for (const s of order) {
      code <<= (lens[s] - prev);
      prev = lens[s];
      rows.push('  ' + api.esc(String.fromCharCode(s))
        + '  ' + String(count[s]).padStart(3) + '회  '
        + lens[s] + '비트  ' + code.toString(2).padStart(lens[s], '0'));
      bits += count[s] * lens[s];
      code++;
    }
    let h = 0;
    for (const s of syms) {
      const p = count[s] / src.length;
      h -= p * Math.log2(p);
    }
    api.w(host, rows.join('\n')
      + '\n\n평균 길이  <span class="ok">'
      + (bits / src.length).toFixed(3) + ' 비트</span>'
      + '   엔트로피  ' + h.toFixed(3) + ' 비트'
      + '\n본문  ' + Math.ceil(bits / 8) + ' 바이트  (원본 '
      + src.length + ' 바이트, 부호표 제외)');
  };
  bind(host, run);
});

// ── 5부 · 구간 축소 ───────────────────────────────────────────────
__demo('interval', (host, api) => {
  const run = () => {
    const p0raw = Number(val(host, 'p', '0.8'));
    const seq = val(host, 'bits', '0001').replace(/[^01]/g, '');
    const p0 = Math.min(0.99, Math.max(0.01, isFinite(p0raw) ? p0raw : 0.8));
    if (!seq.length) {
      api.w(host, '0 과 1 로 된 비트열을 넣어 보세요', 'dim');
      return;
    }
    let lo = 0;
    let w = 1;
    const rows: string[] = [];
    for (const b of seq.slice(0, 12)) {
      const bound = w * p0;
      if (b === '0') {
        w = bound;
      } else {
        lo += bound;
        w -= bound;
      }
      rows.push('  ' + b + '  [' + lo.toFixed(6) + ', '
        + (lo + w).toFixed(6) + ')   폭 ' + w.toExponential(3));
    }
    const bits = -Math.log2(w);
    api.w(host, 'p(0) = ' + p0.toFixed(2) + '\n' + rows.join('\n')
      + '\n\n필요한 비트  <span class="ok">' + bits.toFixed(3)
      + '</span>   (허프만이라면 ' + seq.length + '비트)'
      + '\n한 비트당  ' + (bits / seq.length).toFixed(3) + '비트');
  };
  bind(host, run);
});

// ── 7부 · LZ77 토큰 ───────────────────────────────────────────────
__demo('lz77', (host, api) => {
  const run = () => {
    const text = val(host, 'text', 'abcabcabcabd');
    const src = bytesOf(text).slice(0, 64);
    if (!src.length) {
      api.w(host, '글자를 넣어 보세요', 'dim');
      return;
    }
    const rows: string[] = [];
    let lits = 0;
    let matches = 0;
    let i = 0;
    while (i < src.length) {
      let bl = 0;
      let bd = 0;
      for (let d = 1; d <= i; d++) {
        let l = 0;
        while (i + l < src.length && src[i - d + l] === src[i + l]
               && l < 255) {
          l++;
        }
        if (l > bl) {
          bl = l;
          bd = d;
        }
      }
      if (bl >= 3) {
        rows.push('  ' + String(i).padStart(3) + '  일치   거리 ' + bd
          + ' 길이 ' + bl + '  → '
          + api.esc(text.slice(i, i + bl)));
        matches++;
        i += bl;
      } else {
        rows.push('  ' + String(i).padStart(3) + '  리터럴 '
          + api.esc(String.fromCharCode(src[i])));
        lits++;
        i++;
      }
    }
    const bytes = lits + matches * 3 + Math.ceil((lits + matches) / 8);
    api.w(host, rows.join('\n')
      + '\n\n리터럴 ' + lits + ' · 일치 ' + matches
      + '\n원본 ' + src.length + ' → <span class="'
      + (bytes < src.length ? 'ok' : 'bad') + '">' + bytes
      + ' 바이트</span>  (리터럴 1 · 일치 3 · 플래그 8개마다 1)');
  };
  bind(host, run);
});

// ── 10부 · BWT ────────────────────────────────────────────────────
__demo('bwt', (host, api) => {
  const run = () => {
    const text = val(host, 'text', 'banana').slice(0, 16);
    const src = bytesOf(text).slice(0, 16);
    if (src.length < 2) {
      api.w(host, '두 글자 이상 넣어 보세요', 'dim');
      return;
    }
    const n = src.length;
    const rots: Array<{ k: number; s: string }> = [];
    for (let k = 0; k < n; k++) {
      let s = '';
      for (let j = 0; j < n; j++) s += String.fromCharCode(src[(k + j) % n]);
      rots.push({ k: k, s: s });
    }
    rots.sort((a, b) => (a.s < b.s ? -1 : a.s > b.s ? 1 : 0));
    let last = '';
    let primary = 0;
    const rows: string[] = [];
    for (let r = 0; r < rots.length; r++) {
      last += rots[r].s[n - 1];
      if (rots[r].k === 0) primary = r;
      rows.push('  ' + (rots[r].k === 0 ? '→' : ' ') + ' '
        + api.esc(rots[r].s));
    }
    // 같은 글자가 얼마나 뭉쳤나
    let runs = 1;
    for (let i = 1; i < last.length; i++) {
      if (last[i] !== last[i - 1]) runs++;
    }
    api.w(host, rows.join('\n')
      + '\n\n마지막 열  <span class="ok">' + api.esc(last) + '</span>'
      + '   원본 자리 ' + primary
      + '\n토막 수  ' + runs + ' / ' + n
      + '  — 적을수록 뒤의 MTF 가 0 을 많이 낸다');
  };
  bind(host, run);
});

// ── 13부 · 양자화 ─────────────────────────────────────────────────
__demo('quantise', (host, api) => {
  const run = () => {
    const q = Math.max(1, Math.min(255,
      Math.floor(Number(val(host, 'q', '16')))));
    const coeffs = [240, -93, 41, -18, 9, -5, 3, -2, 1, 0, 0, 0];
    const rows: string[] = [];
    let zeros = 0;
    let err = 0;
    for (const v of coeffs) {
      const dead = v < 0 ? -Math.floor(-v / q) : Math.floor(v / q);
      const back = dead * q;
      if (dead === 0) zeros++;
      err += Math.abs(v - back);
      rows.push('  ' + String(v).padStart(5) + ' / ' + q + ' = '
        + String(dead).padStart(4) + '  → 되돌리면 '
        + String(back).padStart(5)
        + '  (오차 ' + Math.abs(v - back) + ')');
    }
    api.w(host, rows.join('\n')
      + '\n\n0 이 된 계수  <span class="ok">' + zeros + '</span> / '
      + coeffs.length
      + '\n오차 합  <span class="' + (err > 200 ? 'bad' : 'ok') + '">'
      + err + '</span>'
      + '\n\nq 를 키우면 0 이 늘고(작아지고) 오차도 는다.'
      + ' 이 맞바꿈이 손실 압축의 전부다.');
  };
  bind(host, run);
});
