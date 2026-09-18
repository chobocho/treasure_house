"use strict";
// 이 덱의 데모 아홉 — 조립기가 덱 끝의 <script> 에 그대로 넣는다.
// 외부 라이브러리 없이 순수 자바스크립트. 알고리즘은 부록 A(19부)의
// mygit 파이썬 판을 옮긴 것이고, 정답은 check_deck.js 의 CASES 가
// 진짜 git·golden/ 이 낸 값과 견준다(PLAN.md §5 11단계).
//
// 입력칸은 data-<이름> 으로 표시한다. check_deck.js 의 DOM 스텁이 그
// 모양을 보고 값을 넣어 주므로, 모양을 바꾸면 검사가 기본값만 보게 된다.

function val(host, name, dflt) {
  var el = host.querySelector('[data-' + name + ']');
  var v = el && el.value;
  return (v === undefined || v === null || v === '') ? dflt : String(v);
}
function flag(host, name, dflt) {
  var el = host.querySelector('[data-' + name + ']');
  if (!el || el.checked === undefined) return dflt;
  return !!el.checked;
}
function bind(host, run) {
  var go = host.querySelector('button');
  if (go && go.addEventListener) go.addEventListener('click', run);
  var ins = host.querySelectorAll('input, textarea, select');
  for (var i = 0; i < ins.length; i++) {
    ins[i].addEventListener('input', run);
    ins[i].addEventListener('change', run);
  }
  run();
}
// 글자 → UTF-8 바이트. git 은 파일을 바이트로 본다.
function utf8(text) {
  var out = [];
  for (var i = 0; i < text.length; i++) {
    var c = text.codePointAt(i);
    if (c > 0xffff) i++;
    if (c < 0x80) out.push(c);
    else if (c < 0x800) out.push(0xc0 | (c >> 6), 0x80 | (c & 63));
    else if (c < 0x10000) {
      out.push(0xe0 | (c >> 12), 0x80 | ((c >> 6) & 63), 0x80 | (c & 63));
    } else {
      out.push(0xf0 | (c >> 18), 0x80 | ((c >> 12) & 63),
        0x80 | ((c >> 6) & 63), 0x80 | (c & 63));
    }
  }
  return out;
}
function hex2(b) { return (b < 16 ? '0' : '') + b.toString(16); }

// ── SHA-1 (19부 1단계의 JS 판) — O(n) 시간, O(1) 추가 공간 ──────────
function sha1Hex(bytes) {
  var h = [0x67452301, 0xefcdab89, 0x98badcfe, 0x10325476, 0xc3d2e1f0];
  var n = bytes.length;
  var msg = bytes.slice();
  msg.push(0x80);
  while (msg.length % 64 !== 56) msg.push(0);
  // 비트 길이 64비트 빅 엔디언 — 2^53 아래이므로 나눗셈으로 충분
  var bits = n * 8;
  var hi = Math.floor(bits / 0x100000000), lo = bits >>> 0;
  msg.push((hi >>> 24) & 255, (hi >>> 16) & 255, (hi >>> 8) & 255, hi & 255,
    (lo >>> 24) & 255, (lo >>> 16) & 255, (lo >>> 8) & 255, lo & 255);
  var w = new Array(80);
  var rotl = function (x, s) { return (x << s) | (x >>> (32 - s)); };
  for (var off = 0; off < msg.length; off += 64) {
    for (var t = 0; t < 16; t++) {
      var p = off + 4 * t;
      w[t] = (msg[p] << 24) | (msg[p + 1] << 16) | (msg[p + 2] << 8) | msg[p + 3];
    }
    for (t = 16; t < 80; t++) w[t] = rotl(w[t - 3] ^ w[t - 8] ^ w[t - 14] ^ w[t - 16], 1);
    var a = h[0], b = h[1], c = h[2], d = h[3], e = h[4];
    for (t = 0; t < 80; t++) {
      var f, k;
      if (t < 20) { f = (b & c) | (~b & d); k = 0x5a827999; }
      else if (t < 40) { f = b ^ c ^ d; k = 0x6ed9eba1; }
      else if (t < 60) { f = (b & c) | (b & d) | (c & d); k = 0x8f1bbcdc; }
      else { f = b ^ c ^ d; k = 0xca62c1d6; }
      var tmp = (rotl(a, 5) + f + e + k + w[t]) | 0;
      e = d; d = c; c = rotl(b, 30); b = a; a = tmp;
    }
    h[0] = (h[0] + a) | 0; h[1] = (h[1] + b) | 0; h[2] = (h[2] + c) | 0;
    h[3] = (h[3] + d) | 0; h[4] = (h[4] + e) | 0;
  }
  return h.map(function (x) { return ('00000000' + (x >>> 0).toString(16)).slice(-8); }).join('');
}

// ── 줄 나누기와 Myers 앞방향 (19부 8단계, 밀어 붙이기는 뺐다) ──────
function splitLines(text) {
  if (!text) return [];
  var parts = text.split('\n');
  var out = parts.slice(0, -1).map(function (p) { return p + '\n'; });
  if (parts[parts.length - 1]) out.push(parts[parts.length - 1]);
  return out;
}
// (ra, rb) — 줄마다 바뀌었나. O((N+M)·D)
function myersFlags(a, b) {
  var n = a.length, m = b.length, s = 0, e = 0;
  while (s < n && s < m && a[s] === b[s]) s++;
  while (e < n - s && e < m - s && a[n - 1 - e] === b[m - 1 - e]) e++;
  var A = a.slice(s, n - e), B = b.slice(s, m - e), N = A.length, M = B.length;
  var v = { 1: 0 }, trace = [], dEnd = -1;
  outer:
  for (var d = 0; d <= N + M; d++) {
    trace.push(Object.assign({}, v));
    for (var k = -d; k <= d; k += 2) {
      var x = (k === -d || (k !== d && v[k - 1] < v[k + 1])) ? v[k + 1] : v[k - 1] + 1;
      var y = x - k;
      while (x < N && y < M && A[x] === B[y]) { x++; y++; }
      v[k] = x;
      if (x >= N && y >= M) { dEnd = d; break outer; }
    }
  }
  var ra = new Array(N).fill(false), rb = new Array(M).fill(false);
  var X = N, Y = M;
  for (d = dEnd; d > 0; d--) {
    var vv = trace[d], kk = X - Y;
    var down = (kk === -d || (kk !== d && vv[kk - 1] < vv[kk + 1]));
    var pk = down ? kk + 1 : kk - 1, px = vv[pk], py = px - pk;
    while (X > px + (down ? 0 : 1) && Y > py + (down ? 1 : 0)) { X--; Y--; }
    if (down) { Y--; rb[Y] = true; } else { X--; ra[X] = true; }
  }
  var pad = function (r, len) { return new Array(s).fill(false).concat(r, new Array(len).fill(false)); };
  return [pad(ra, e), pad(rb, e)];
}
// 바뀐 곳 [a 자리, b 자리, a 줄 수, b 줄 수] — git 의 xdl_build_script
function buildChanges(ra, rb) {
  var out = [], i1 = ra.length, i2 = rb.length;
  while (i1 > 0 || i2 > 0) {
    if ((i1 > 0 && ra[i1 - 1]) || (i2 > 0 && rb[i2 - 1])) {
      var l1 = i1, l2 = i2;
      while (i1 > 0 && ra[i1 - 1]) i1--;
      while (i2 > 0 && rb[i2 - 1]) i2--;
      out.push([i1, i2, l1 - i1, l2 - i2]);
    } else { i1--; i2--; }
  }
  return out.reverse();
}
function span(start, count) {
  var first = count ? start + 1 : start;
  return count === 1 ? String(first) : first + ',' + count;
}
function unified(a, b) {
  var f = myersFlags(a, b), ch = buildChanges(f[0], f[1]), out = [], C = 3;
  for (var i = 0; i < ch.length;) {
    var j = i;
    while (j + 1 < ch.length && ch[j + 1][0] - (ch[j][0] + ch[j][2]) <= 2 * C) j++;
    var s1 = Math.max(ch[i][0] - C, 0), s2 = Math.max(ch[i][1] - C, 0);
    var e1 = Math.min(ch[j][0] + ch[j][2] + C, a.length);
    var e2 = Math.min(ch[j][1] + ch[j][3] + C, b.length);
    out.push('@@ -' + span(s1, e1 - s1) + ' +' + span(s2, e2 - s2) + ' @@');
    var p1 = s1;
    for (var q = i; q <= j; q++) {
      var c = ch[q], z;
      for (z = p1; z < c[0]; z++) out.push(' ' + a[z]);
      for (z = c[0]; z < c[0] + c[2]; z++) out.push('-' + a[z]);
      for (z = c[1]; z < c[1] + c[3]; z++) out.push('+' + b[z]);
      p1 = c[0] + c[2];
    }
    for (z = p1; z < e1; z++) out.push(' ' + a[z]);
    i = j + 1;
  }
  return out.map(function (l) { return l.replace(/\n$/, ''); });
}

// ── 3-way 합치기 (19부 10단계, git 의 xdl_merge ZEALOUS 를 옮김) ────
function changesOf(a, b) { var f = myersFlags(a, b); return buildChanges(f[0], f[1]); }
function sideRange(cs, start, end) {
  var s = start, e = end;
  cs.forEach(function (c) { if (c[0] < start) s += c[3] - c[2]; if (c[0] <= end) e += c[3] - c[2]; });
  return [s, e];
}
function same(x, y) { return x.length === y.length && x.every(function (v, i) { return v === y[i]; }); }
function merge3(base, ours, theirs, label) {
  var b = splitLines(base), o = splitLines(ours), t = splitLines(theirs);
  if (ours === theirs || base === theirs) return [o, 0];
  if (base === ours) return [t, 0];
  var c1 = changesOf(b, o), c2 = changesOf(b, t), i = 0, j = 0, pieces = [], pos = 0;
  var push = function (s, e, kind, ol, tl) {
    if (s > pos) pieces.push(['same', b.slice(pos, s)]);
    if (kind === 'o') pieces.push(['same', ol]);
    else if (kind === 't') pieces.push(['same', tl]);
    else refine(ol, tl).forEach(function (p) { pieces.push(p); });
    pos = e;
  };
  while (i < c1.length || j < c2.length) {
    var x = c1[i], y = c2[j];
    if (!y || (x && x[0] + x[2] < y[0])) { push(x[0], x[0] + x[2], 'o', o.slice(x[1], x[1] + x[3])); i++; continue; }
    if (!x || y[0] + y[2] < x[0]) { push(y[0], y[0] + y[2], 't', null, t.slice(y[1], y[1] + y[3])); j++; continue; }
    if (x[0] === y[0] && x[2] === y[2] && same(o.slice(x[1], x[1] + x[3]), t.slice(y[1], y[1] + y[3]))) {
      push(x[0], x[0] + x[2], 'o', o.slice(x[1], x[1] + x[3])); i++; j++; continue;
    }
    var start = Math.min(x[0], y[0]), end = Math.max(x[0] + x[2], y[0] + y[2]);
    i++; j++;
    for (;;) {
      if (i < c1.length && c1[i][0] <= end) { end = Math.max(end, c1[i][0] + c1[i][2]); i++; }
      else if (j < c2.length && c2[j][0] <= end) { end = Math.max(end, c2[j][0] + c2[j][2]); j++; }
      else break;
    }
    var os = sideRange(c1, start, end), ts = sideRange(c2, start, end);
    push(start, end, 'c', o.slice(os[0], os[1]), t.slice(ts[0], ts[1]));
  }
  if (pos < b.length) pieces.push(['same', b.slice(pos)]);
  var joined = [];
  pieces.forEach(function (p) {
    var n = joined.length;
    if (p[0] === 'conf' && n >= 2 && joined[n - 1][0] === 'same' && joined[n - 2][0] === 'conf' && joined[n - 1][1].length <= 3) {
      var mid = joined.pop()[1], prev = joined.pop();
      p = ['conf', prev[1].concat(mid, p[1]), prev[2].concat(mid, p[2])];
    } else if (p[0] === 'same' && n && joined[n - 1][0] === 'same') {
      p = ['same', joined.pop()[1].concat(p[1])];
    }
    joined.push(p);
  });
  var out = [], conflicts = 0;
  joined.forEach(function (p) {
    if (p[0] === 'conf') {
      conflicts++;
      out = out.concat(['<<<<<<< HEAD\n'], p[1], ['=======\n'], p[2], ['>>>>>>> ' + label + '\n']);
    } else out = out.concat(p[1]);
  });
  return [out, conflicts];
}
function refine(o, t) {
  if (same(o, t)) return [['same', o]];
  var out = [], p1 = 0;
  changesOf(o, t).forEach(function (c) {
    if (c[0] > p1) out.push(['same', o.slice(p1, c[0])]);
    out.push(['conf', o.slice(c[0], c[0] + c[2]), t.slice(c[1], c[1] + c[3])]);
    p1 = c[0] + c[2];
  });
  if (p1 < o.length) out.push(['same', o.slice(p1)]);
  return out;
}

// ── 3부 · 객체 이름 ────────────────────────────────────────────────
__demo('sha1', function (host, api) {
  bind(host, function () {
    var text = val(host, 'text', 'abc');
    var bytes = utf8(text);
    api.w(host, '입력 ' + bytes.length + '바이트\nSHA-1  <span class="ok">' + sha1Hex(bytes) + '</span>');
  });
});

__demo('objhdr', function (host, api) {
  bind(host, function () {
    var text = val(host, 'text', 'hello');
    var body = utf8(text);
    if (flag(host, 'nl', true)) body.push(10);
    var head = utf8('blob ' + body.length).concat([0]);
    var all = head.concat(body);
    var shown = all.slice(0, 48).map(function (b) {
      if (b === 0) return '\\0';
      if (b === 10) return '\\n';
      return b >= 32 && b < 127 ? String.fromCharCode(b) : '\\x' + hex2(b);
    }).join('');
    api.w(host, '머리  "blob ' + body.length + '\\0"  (' + head.length + '바이트)\n' +
      '바이트 ' + api.esc(shown) + (all.length > 48 ? '…' : '') + '\n' +
      '이름  <span class="ok">' + sha1Hex(all) + '</span>');
  });
});

__demo('treesort', function (host, api) {
  bind(host, function () {
    var names = val(host, 'names', 'ab a=b a/ a.b a-b').split(/\s+/).filter(Boolean);
    // 끝에 / 를 붙인 이름은 하위 트리. 열쇠는 이름 + '/', 비교는 바이트
    var ents = names.map(function (n) {
      var dir = /\/$/.test(n), name = dir ? n.slice(0, -1) : n;
      return { shown: n, key: utf8(dir ? name + '/' : name) };
    });
    ents.sort(function (x, y) {
      for (var i = 0; i < Math.min(x.key.length, y.key.length); i++) {
        if (x.key[i] !== y.key[i]) return x.key[i] - y.key[i];
      }
      return x.key.length - y.key.length;
    });
    api.w(host, '트리 차례  <span class="ok">' + api.esc(ents.map(function (e) { return e.shown; }).join(' · ')) + '</span>\n' +
      ents.map(function (e) { return '  ' + api.esc(e.shown).padEnd(10) + ' ' + e.key.map(hex2).join(' '); }).join('\n'));
  });
});

// ── 7부 · 머지 ─────────────────────────────────────────────────────
__demo('merge3', function (host, api) {
  bind(host, function () {
    var base = val(host, 'base', 'a\nb\nc\n');
    var ours = val(host, 'ours', 'a\nb2\nc\n');
    var theirs = val(host, 'theirs', 'a\nB\nc\n');
    var r = merge3(base, ours, theirs, 'theirs');
    api.w(host, (r[1] ? '<span class="bad">충돌 ' + r[1] + '곳</span>' : '<span class="ok">깨끗하게 합쳐짐</span>') + '\n' +
      api.esc(r[0].join('').replace(/\n$/, '')));
  });
});

// git 7부 dag 실험의 역사 그대로(out/dag__log-all-format-h-p-s.txt)
var DAG = {
  A: [], B: ['A'], C: ['B'], D: ['A'], M1: ['C', 'D'], M2: ['D', 'C'], G: ['M1'], H: ['M2'],
};
var DAG_ID = { A: '8d60d2f', B: '2c14ef0', C: 'b4072b3', D: '2e14562', M1: 'faa265d',
  M2: '32d4394', G: '0df6e0c', H: '11faaa9' };
function ancestors(x) {
  var seen = {}, st = [x];
  while (st.length) { var c = st.pop(); if (seen[c]) continue; seen[c] = true; st = st.concat(DAG[c]); }
  return seen;
}
__demo('mergebase', function (host, api) {
  bind(host, function () {
    var a = val(host, 'a', 'G'), b = val(host, 'b', 'H');
    if (!DAG[a] || !DAG[b]) { api.w(host, 'A·B·C·D·M1·M2·G·H 가운데서 고르세요', 'bad'); return; }
    var aa = ancestors(a), bb = ancestors(b), common = Object.keys(aa).filter(function (c) { return bb[c]; });
    var below = {};
    common.forEach(function (c) { DAG[c].forEach(function (p) { Object.assign(below, ancestors(p)); }); });
    var best = common.filter(function (c) { return !below[c]; }).sort();
    api.w(host, '공통 조상  ' + common.sort().join(' ') + '\nmerge-base  <span class="ok">' +
      best.map(function (c) { return c + '(' + DAG_ID[c] + ')'; }).join(' ') + '</span>' +
      (best.length > 1 ? '\n둘 이상 — 교차 머지' : ''));
  });
});

// ── 9부 · diff ─────────────────────────────────────────────────────
__demo('myers', function (host, api) {
  bind(host, function () {
    var a = splitLines(val(host, 'a', 'a\nb\nc\nd\n'));
    var b = splitLines(val(host, 'b', 'a\nx\nc\nd\ne\n'));
    var f = myersFlags(a, b);
    var del = f[0].filter(Boolean).length, ins = f[1].filter(Boolean).length;
    api.w(host, '지운 줄 ' + del + ' · 끼운 줄 ' + ins + ' · 편집 D = ' + (del + ins) + '\n' +
      unified(a, b).map(api.esc).join('\n'));
  });
});

// ── 10부 · 델타 ────────────────────────────────────────────────────
// golden/pack/ofs.pack 의 첫 델타(out/demo_delta__python3-delta.py.txt)
var REAL_DELTA = 'ff23de23b06a1174342e300a657874726120342e310a657874726120342e320a' +
  '657874726120342e330a657874726120342e340a657874726120342e350a6578' +
  '74726120342e360a657874726120342e370a657874726120342e380a65787472' +
  '6120342e390a657874726120342e31300a657874726120342e31310a';
__demo('delta', function (host, api) {
  bind(host, function () {
    var h = val(host, 'hex', REAL_DELTA).replace(/[^0-9a-fA-F]/g, '');
    var d = [];
    for (var i = 0; i + 1 < h.length; i += 2) d.push(parseInt(h.substr(i, 2), 16));
    var q = 0;
    var varint = function () {
      var n = 0, s = 0, byte;
      do { if (q >= d.length) throw new Error('델타가 중간에 끊겼다'); byte = d[q++]; n += (byte & 0x7f) * Math.pow(2, s); s += 7; } while (byte & 0x80);
      return n;
    };
    try {
      var src = varint(), dst = varint(), rows = [], made = 0;
      while (q < d.length) {
        var op = d[q++];
        if (op & 0x80) {
          var off = 0, n = 0, k;
          for (k = 0; k < 4; k++) if (op & (1 << k)) off += d[q++] * Math.pow(256, k);
          for (k = 0; k < 3; k++) if (op & (0x10 << k)) n += d[q++] * Math.pow(256, k);
          if (!n) n = 0x10000;
          rows.push('  복사  자리 ' + off + ' 에서 ' + n + '바이트');
          made += n;
        } else if (op) {
          rows.push('  끼움  ' + op + '바이트');
          q += op; made += op;
        } else throw new Error('명령 0 은 쓰지 않는다');
      }
      api.w(host, '바탕 크기 <span class="ok">' + src + '</span> · 결과 크기 <span class="ok">' + dst + '</span>\n' +
        rows.join('\n') + '\n명령으로 만든 길이 ' + made + (made === dst ? ' = 결과 크기' : ' ≠ 결과 크기'));
    } catch (e) { api.w(host, api.esc(e.message), 'bad'); }
  });
});

// ── 11부 · pkt-line ────────────────────────────────────────────────
__demo('pktline', function (host, api) {
  bind(host, function () {
    var raw = val(host, 'text', 'version 2\\n');
    var text = raw.replace(/\\n/g, '\n');
    var n = utf8(text).length + 4;
    var len = ('0000' + n.toString(16)).slice(-4);
    api.w(host, '길이 ' + n + ' = 데이터 ' + (n - 4) + ' + 머리 4\npkt-line  <span class="ok">' +
      api.esc(len + raw) + '</span>');
  });
});

// ── 13부 · .gitignore ─────────────────────────────────────────────
// 규칙의 부분집합: # 주석, ! 뒤집기, 끝 / 는 디렉터리만, 앞 / 또는 가운데
// / 는 뿌리 기준, 그 밖은 어느 깊이의 이름에나, * ? 와 ** 를 안다.
function globRe(p) {
  var s = '';
  for (var i = 0; i < p.length; i++) {
    var c = p[i];
    if (c === '*' && p[i + 1] === '*') {
      if (p[i + 2] === '/') { s += '(?:.*/)?'; i += 2; } else { s += '.*'; i++; }
    } else if (c === '*') s += '[^/]*';
    else if (c === '?') s += '[^/]';
    else s += c.replace(/[.+^${}()|[\]\\]/g, '\\$&');
  }
  return s;
}
function ignoreVerdict(rules, path) {
  var parts = path.split('/'), hit = null;
  // 경로 자신과 그 위 디렉터리들을 각각 규칙에 대 본다 — 디렉터리가 무시되면 안의 파일도
  for (var depth = 1; depth <= parts.length; depth++) {
    var cand = parts.slice(0, depth).join('/'), isDir = depth < parts.length;
    for (var r = 0; r < rules.length; r++) {
      var rule = rules[r], pat = rule.pat;
      if (rule.dirOnly && !isDir) continue;
      var anchored = pat.indexOf('/') >= 0;
      var re = anchored ? new RegExp('^' + globRe(pat.replace(/^\//, '')) + '$')
        : new RegExp('(?:^|/)' + globRe(pat) + '$');
      if (re.test(cand)) hit = rule;
    }
    if (hit && !hit.neg && isDir) return hit;
    if (isDir) hit = null;
  }
  return hit;
}
__demo('ignore', function (host, api) {
  bind(host, function () {
    var rules = val(host, 'rules', '*.log\n!keep.log\nbuild/\n/root.txt\ndoc/**/*.tmp').split('\n')
      .map(function (l, i) { return { line: i + 1, raw: l.trim() }; })
      .filter(function (r) { return r.raw && r.raw[0] !== '#'; })
      .map(function (r) {
        var p = r.raw, neg = p[0] === '!';
        if (neg) p = p.slice(1);
        var dirOnly = /\/$/.test(p);
        return { line: r.line, raw: r.raw, neg: neg, dirOnly: dirOnly, pat: dirOnly ? p.slice(0, -1) : p };
      });
    var paths = val(host, 'paths', 'a.log\nkeep.log\nbuild/x.o\nsrc/build\nsub/root.txt\ndoc/c.tmp').split('\n')
      .map(function (s) { return s.trim(); }).filter(Boolean);
    api.w(host, paths.map(function (p) {
      var h = ignoreVerdict(rules, p);
      if (!h) return '  ' + api.esc(p).padEnd(16) + ' 추적 대상';
      return '  ' + api.esc(p).padEnd(16) + (h.neg ? ' 무시 안 함' : ' <span class="bad">무시</span>') +
        '  (' + h.line + '행 ' + api.esc(h.raw) + ')';
    }).join('\n'));
  });
});
