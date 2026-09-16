/* 이 덱의 데모들 — 조립기가 tail.html 의 <!--DEMOS--> 자리에 넣는다.
 * (wireless/deck/demos.js 의 규칙을 물려받았다.)
 *
 *   1. 파이썬 참조와 같은 식을 쓴다. py/transformerlib 가 진짜이고 여기는
 *      손으로 만져 보게 한 것이다. 식이 갈라지면 deck/check_deck.js 의
 *      CASES 가 잡는다 — 거기 적힌 기댓값은 파이썬이 낸 값이다.
 *   2. 빈 입력에서 죽지 않는다. 숫자를 못 읽으면 기본값으로 간다.
 *   3. 처음 배선될 때 한 번 그린다.
 */
(function () {
  'use strict';

  function nv(host, key, dflt) {
    var e = host.querySelector('[data-' + key + ']');
    if (!e) return dflt;
    var v = parseFloat(e.value);
    return isFinite(v) ? v : dflt;
  }
  function sv(host, key, dflt) {
    var e = host.querySelector('[data-' + key + ']');
    if (!e || !e.value) return dflt;
    return String(e.value);
  }
  function bv(host, key) {
    var e = host.querySelector('[data-' + key + ']');
    return !!(e && e.checked);
  }
  function f(x, n) {
    if (!isFinite(x)) return '—';
    return x.toFixed(n === undefined ? 4 : n);
  }
  function nums(s) {
    return String(s).split(/[\s,]+/).map(parseFloat)
      .filter(function (v) { return isFinite(v); });
  }
  function wire(host, draw) {
    var list = host.querySelectorAll('input, select, button, textarea');
    for (var i = 0; i < list.length; i++) {
      list[i].addEventListener('input', draw);
      list[i].addEventListener('change', draw);
      list[i].addEventListener('click', draw);
    }
    draw();
  }
  function pad(s, n) {
    s = String(s);
    while (s.length < n) s = ' ' + s;
    return s;
  }

  // 소프트맥스 — ops._softmax_row 와 같다: 최댓값을 빼고 exp 를 정규화
  function softmax(z) {
    var m = -Infinity, i, s = 0, e = [];
    for (i = 0; i < z.length; i++) if (z[i] > m) m = z[i];
    for (i = 0; i < z.length; i++) { e.push(Math.exp(z[i] - m)); s += e[i]; }
    return e.map(function (v) { return v / s; });
  }

  /* ---- 1. 온도 ---- */
  window.__demo('d-softmax', function (host, api) {
    wire(host, function () {
      var z = nums(sv(host, 'logits', '2 1 0 -1'));
      if (!z.length) z = [0];
      var tau = nv(host, 'tau', 1);
      var lines = ['로짓 ' + z.join(' ') + ' · 온도 ' + tau];
      if (tau <= 0) {
        var best = 0;
        for (var i = 1; i < z.length; i++) if (z[i] > z[best]) best = i;
        lines.push('온도 0 → argmax: 칸 ' + best);
      } else {
        var p = softmax(z.map(function (v) { return v / tau; }));
        for (var j = 0; j < p.length; j++) {
          var k = Math.round(p[j] * 30);
          lines.push('칸 ' + j + ' ' + f(p[j]) + ' '
            + new Array(k + 1).join('#'));
        }
      }
      api.w(host, api.esc(lines.join('\n')));
    });
  });

  /* ---- 2. 어텐션 계산기 ---- */
  // attention.scaled_dot_product 와 같은 식. 행은 줄바꿈이나 ; 로 나눈다.
  function rows(s) {
    return String(s).split(/[;\n]/).map(nums)
      .filter(function (r) { return r.length; });
  }
  window.__demo('d-attn', function (host, api) {
    wire(host, function () {
      var Q = rows(sv(host, 'q', '1 0; 0 1; 1 1'));
      var K = rows(sv(host, 'k', '1 0; 0 1; 1 1'));
      var V = rows(sv(host, 'v', '10 0; 0 10; 5 5'));
      var causal = bv(host, 'causal');
      var n = Math.min(Q.length, K.length, V.length);
      var dk = Q.length ? Q[0].length : 1;
      var lines = ['d_k = ' + dk + ' · 인과 마스크 ' + (causal ? '켬' : '끔')];
      for (var i = 0; i < n; i++) {
        var s = [], lim = causal ? i + 1 : n;
        for (var j = 0; j < lim; j++) {
          var acc = 0;
          for (var c = 0; c < dk; c++) acc += (Q[i][c] || 0) * (K[j][c] || 0);
          s.push(acc / Math.sqrt(dk));
        }
        var w = softmax(s), out = [];
        for (c = 0; c < V[0].length; c++) {
          var o = 0;
          for (j = 0; j < w.length; j++) o += w[j] * (V[j][c] || 0);
          out.push(f(o, 3));
        }
        var ws = [];
        for (j = 0; j < n; j++) ws.push(j < w.length ? f(w[j], 3) : '0.000');
        lines.push('질의 ' + i + ' 가중치 [' + ws.join(' ') + '] → 출력 ['
          + out.join(' ') + ']');
      }
      api.w(host, api.esc(lines.join('\n')));
    });
  });

  /* ---- 3. 사인 위치 인코딩 ---- */
  // posenc.sinusoidal 과 같다: 짝 i 마다 (sin, cos)(p·ωᵢ), ωᵢ = 10000^(−2i/d)
  function sinpe(p, d) {
    var v = [];
    for (var i = 0; i < d / 2; i++) {
      var w = 1 / Math.pow(10000, 2 * i / d);
      v.push(Math.sin(p * w), Math.cos(p * w));
    }
    return v;
  }
  window.__demo('d-sinpe', function (host, api) {
    wire(host, function () {
      var d = Math.round(nv(host, 'dim', 16));
      if (d < 2) d = 2;
      if (d % 2) d += 1;
      if (d > 512) d = 512;
      var p = Math.round(nv(host, 'pos', 3));
      var k = Math.round(nv(host, 'shift', 1));
      var a = sinpe(p, d), b = sinpe(p + k, d), dot = 0;
      for (var i = 0; i < d; i++) dot += a[i] * b[i];
      var lines = ['d = ' + d + ' · 위치 ' + p + ' 의 앞 여덟 칸'];
      var head = [];
      for (i = 0; i < Math.min(8, d); i++) head.push(f(a[i]));
      lines.push('  [' + head.join(' ') + ' …]');
      lines.push('PE(' + p + ') · PE(' + (p + k) + ') = ' + f(dot)
        + '   (같은 간격 ' + k + ' 이면 p 와 상관없이 같다)');
      api.w(host, api.esc(lines.join('\n')));
    });
  });

  /* ---- 4. 파라미터 계산기 ---- */
  // model.count_params(learned) 과 같은 식
  function countParams(V, T, d, L, ff) {
    var block = 4 * d + 3 * d * d + 3 * d + d * d + d + 2 * d * ff + ff + d;
    return { emb: V * d, pos: T * d, block: block, lnf: 2 * d,
      total: V * d + T * d + L * block + 2 * d };
  }
  function comma(n) {
    return String(n).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
  }
  window.__demo('d-params', function (host, api) {
    wire(host, function () {
      var V = Math.max(1, Math.round(nv(host, 'vocab', 50257)));
      var T = Math.max(1, Math.round(nv(host, 'ctx', 1024)));
      var d = Math.max(1, Math.round(nv(host, 'dim', 768)));
      var L = Math.max(0, Math.round(nv(host, 'layers', 12)));
      var ff = Math.max(1, Math.round(nv(host, 'ff', 4 * d)));
      var c = countParams(V, T, d, L, ff);
      var lines = [
        '토큰 임베딩 V·d        ' + pad(comma(c.emb), 16),
        '위치 임베딩 T·d        ' + pad(comma(c.pos), 16),
        '블록 하나              ' + pad(comma(c.block), 16),
        '블록 ' + pad(L, 3) + '개             ' + pad(comma(L * c.block), 16),
        '마지막 LN 2d           ' + pad(comma(c.lnf), 16),
        '합계                   ' + pad(comma(c.total), 16),
        '블록 몫 ' + f(100 * L * c.block / c.total, 1) + ' %'];
      api.w(host, api.esc(lines.join('\n')));
    });
  });

  /* ---- 5. 학습률 일정 ---- */
  // optim.lr_schedule 과 같다
  function lrAt(t, hi, lo, warm, total) {
    if (t <= warm) return hi * t / warm;
    var p = (t - warm) / Math.max(1, total - warm);
    return lo + 0.5 * (hi - lo) * (1 + Math.cos(Math.PI * p));
  }
  window.__demo('d-lr', function (host, api) {
    wire(host, function () {
      var hi = nv(host, 'hi', 6e-3), lo = nv(host, 'lo', 6e-4);
      var warm = Math.max(1, Math.round(nv(host, 'warm', 150)));
      var total = Math.max(1, Math.round(nv(host, 'total', 3000)));
      var t = Math.round(nv(host, 'step', 1000));
      var lines = ['스텝 ' + t + ' 의 학습률 ' + lrAt(t, hi, lo, warm, total)
        .toExponential(3), ''];
      for (var r = 0; r <= 10; r++) {
        var s = Math.max(1, Math.round(total * r / 10));
        var v = lrAt(s, hi, lo, warm, total);
        var k = hi > 0 ? Math.round(40 * v / hi) : 0;
        lines.push(pad(s, 6) + ' ' + v.toExponential(2) + ' '
          + new Array(Math.max(0, k) + 1).join('#'));
      }
      api.w(host, api.esc(lines.join('\n')));
    });
  });

  /* ---- 6. top-k · top-p ---- */
  // sample.filtered 와 같다: 온도 → 소프트맥스 → 상위 k → 재정규화 → 누적 p
  function filtered(z, tau, k, p) {
    var q = softmax(z.map(function (v) { return v / tau; }));
    var order = q.map(function (_, i) { return i; });
    order.sort(function (a, b) { return q[b] - q[a] || a - b; });
    if (k > 0) order = order.slice(0, k);
    var s = 0, i;
    for (i = 0; i < order.length; i++) s += q[order[i]];
    var kept = order.map(function (i) { return [i, q[i] / s]; });
    if (p > 0 && p < 1) {
      var acc = 0;
      for (i = 0; i < kept.length; i++) {
        acc += kept[i][1];
        if (acc >= p) { kept = kept.slice(0, i + 1); break; }
      }
      s = 0;
      for (i = 0; i < kept.length; i++) s += kept[i][1];
      kept = kept.map(function (e) { return [e[0], e[1] / s]; });
    }
    return kept;
  }
  window.__demo('d-topk', function (host, api) {
    wire(host, function () {
      var z = nums(sv(host, 'logits', '3 2.5 2 1 0 -1'));
      if (!z.length) z = [0];
      var tau = nv(host, 'tau', 1);
      if (tau <= 0) tau = 1e-6;
      var k = Math.round(nv(host, 'k', 0)), p = nv(host, 'p', 0);
      var kept = filtered(z, tau, k, p);
      var lines = ['남은 후보 ' + kept.length + '개 (온도 ' + tau
        + ' · k ' + (k > 0 ? k : '끔') + ' · p ' + (p > 0 && p < 1 ? p : '끔') + ')'];
      for (var i = 0; i < kept.length; i++) {
        lines.push('  칸 ' + pad(kept[i][0], 2) + '  ' + f(kept[i][1]) + ' '
          + new Array(Math.round(kept[i][1] * 30) + 1).join('#'));
      }
      api.w(host, api.esc(lines.join('\n')));
    });
  });

  /* ---- 7. 사전 토큰화 ---- */
  // tokenizer.pretokenize 와 같은 결정표 (SPEC §5.2). 글자 단위로 돈다.
  function charClass(c) {
    var o = c.codePointAt(0);
    if (c === ' ') return 'S';
    if (o >= 0x09 && o <= 0x0D) return 'W';
    if (c >= '0' && c <= '9') return 'D';
    if (o < 0x80) return /[A-Za-z]/.test(c) ? 'L' : 'P';
    if ((o >= 0x2000 && o <= 0x206F) || (o >= 0x3000 && o <= 0x303F)
        || (o >= 0xFF00 && o <= 0xFF65)) return 'P';
    return 'L';
  }
  function pretokenize(text) {
    var ch = Array.from(text), cls = ch.map(charClass);
    var n = ch.length, i = 0, out = [];
    while (i < n) {
      var c = cls[i], j;
      if (c === 'S' && i + 1 < n && 'LDP'.indexOf(cls[i + 1]) >= 0) {
        var k = cls[i + 1];
        j = i + 2;
        while (j < n && cls[j] === k) j++;
      } else if (c === 'S' || c === 'W') {
        j = i + 1;
        while (j < n && (cls[j] === 'S' || cls[j] === 'W')) j++;
        if (j < n && 'LDP'.indexOf(cls[j]) >= 0 && ch[j - 1] === ' '
            && j - i >= 2) j--;
      } else {
        j = i + 1;
        while (j < n && cls[j] === c) j++;
      }
      out.push(ch.slice(i, j).join(''));
      i = j;
    }
    return out;
  }
  window.__demo('d-pretok', function (host, api) {
    wire(host, function () {
      var text = sv(host, 'text', '김 첨지는  오늘 2원을 벌었다!');
      var parts = pretokenize(text);
      var lines = ['조각 ' + parts.length + '개 — 조각 경계를 | 로 보였다',
        '|' + parts.join('|') + '|', '',
        '부류  ' + parts.map(function (s) {
          return Array.from(s).map(charClass).join('');
        }).join('|')];
      api.w(host, api.esc(lines.join('\n')));
    });
  });

  /* ---- 8. 덧셈 모델 추론 ---- */
  // 8부에서 C 로 학습한 ckpt/c_add.ckpt 를 float16 으로 줄여 실었다
  // (tools/export_js.py). 순전파는 sample.forward_cached 와 같은 차례로
  // 더하고, double 로 계산한다. 가중치가 반올림된 만큼 로짓이 C 와
  // 조금 다르지만 greedy 답은 시험 줄 1000개에서 C 와 같다 —
  // export_js.py --check 가 node 로 전부 대조한다.
  function f16(b64) {
    var bin = atob(b64), n = bin.length / 2, out = new Float64Array(n);
    for (var i = 0; i < n; i++) {
      var h = bin.charCodeAt(2 * i) | (bin.charCodeAt(2 * i + 1) << 8);
      var s = h & 0x8000 ? -1 : 1, e = (h >> 10) & 31, m = h & 1023;
      out[i] = e === 0 ? s * m * Math.pow(2, -24)
        : e === 31 ? (m ? NaN : s * Infinity)
          : s * (1 + m / 1024) * Math.pow(2, e - 15);
    }
    return out;
  }
  function tfmLoad(M) {
    if (M.P) return M;
    var all = f16(M.data), off = 0, P = {};
    for (var i = 0; i < M.shapes.length; i++) {
      var sz = M.shapes[i][1].reduce(function (a, b) { return a * b; }, 1);
      P[M.shapes[i][0]] = all.subarray(off, off + sz);
      off += sz;
    }
    M.P = P;
    return M;
  }
  function lin(x, W, b, nin, nout) {
    var y = new Float64Array(nout), k, j;
    for (k = 0; k < nin; k++)
      for (j = 0; j < nout; j++) y[j] += x[k] * W[k * nout + j];
    for (j = 0; j < nout; j++) y[j] += b[j];
    return y;
  }
  function lnorm(x, g, b) {
    var n = x.length, mu = 0, v = 0, i;
    for (i = 0; i < n; i++) mu += x[i];
    mu /= n;
    for (i = 0; i < n; i++) v += (x[i] - mu) * (x[i] - mu);
    var s = Math.sqrt(v / n + 1e-5), y = new Float64Array(n);
    for (i = 0; i < n; i++) y[i] = g[i] * ((x[i] - mu) / s) + b[i];
    return y;
  }
  function gelu(v) {
    return 0.5 * v * (1 + Math.tanh(0.7978845608028654
      * (v + 0.044715 * v * v * v)));
  }
  // 토큰 하나를 캐시에 더하고 그 자리의 로짓을 돌려준다. 캐시 없이
  // 매번 처음부터 돌려도 답은 같다 — 10부 1장이 보인 성질이다.
  function step(M, tok, cache) {
    var c = M.cfg, P = M.P, d = c.d, h = c.h, dk = d / h, pos = cache.n;
    var x = new Float64Array(d), i, j, t, l;
    for (i = 0; i < d; i++) x[i] = P.wte[tok * d + i] + P.wpe[pos * d + i];
    for (l = 0; l < c.L; l++) {
      var p = 'h' + l + '.';
      var a = lnorm(x, P[p + 'ln1_g'], P[p + 'ln1_b']);
      var qkv = lin(a, P[p + 'Wqkv'], P[p + 'bqkv'], d, 3 * d);
      cache.k[l].push(qkv.slice(d, 2 * d));
      cache.v[l].push(qkv.slice(2 * d));
      var out = new Float64Array(d);
      for (j = 0; j < h; j++) {
        var o = j * dk, s = [];
        for (t = 0; t < cache.k[l].length; t++) {
          var acc = 0;
          for (i = 0; i < dk; i++) acc += qkv[o + i] * cache.k[l][t][o + i];
          s.push(acc / Math.sqrt(dk));
        }
        var w = softmax(s);
        for (t = 0; t < w.length; t++)
          for (i = 0; i < dk; i++) out[o + i] += w[t] * cache.v[l][t][o + i];
      }
      var ao = lin(out, P[p + 'Wo'], P[p + 'bo'], d, d);
      for (i = 0; i < d; i++) x[i] += ao[i];
      var m = lnorm(x, P[p + 'ln2_g'], P[p + 'ln2_b']);
      var hid = lin(m, P[p + 'W1'], P[p + 'b1'], d, c.d_ff);
      for (i = 0; i < c.d_ff; i++) hid[i] = gelu(hid[i]);
      var fo = lin(hid, P[p + 'W2'], P[p + 'b2'], c.d_ff, d);
      for (i = 0; i < d; i++) x[i] += fo[i];
    }
    cache.n++;
    x = lnorm(x, P.lnf_g, P.lnf_b);
    var logits = [];
    for (t = 0; t < c.V; t++) {
      var z = 0;
      for (i = 0; i < d; i++) z += x[i] * P.wte[t * d + i];
      logits.push(z);
    }
    return logits;
  }
  // 프롬프트 글자열 → greedy 로 n 글자. 같은 값이면 작은 id (SPEC §7).
  function greedy(M, prompt, n) {
    tfmLoad(M);
    var cache = { k: [], v: [], n: 0 }, l, i, logits = null, out = '';
    for (l = 0; l < M.cfg.L; l++) { cache.k.push([]); cache.v.push([]); }
    for (i = 0; i < prompt.length; i++) {
      var id = M.vocab.indexOf(prompt[i]);
      if (id < 0) return null;
      logits = step(M, id, cache);
    }
    for (i = 0; i < n && cache.n < M.cfg.T; i++) {
      var best = 0;
      for (var t = 1; t < logits.length; t++) if (logits[t] > logits[best]) best = t;
      out += M.vocab[best];
      if (i + 1 < n && cache.n < M.cfg.T) logits = step(M, best, cache);
    }
    return out;
  }
  window.__tfmGreedy = greedy;
  window.__demo('d-add', function (host, api) {
    wire(host, function () {
      var M = window.__TFM_ADD;
      if (!M) { api.w(host, api.esc('모델이 실리지 않았습니다')); return; }
      var a = Math.round(nv(host, 'a', 763)), b = Math.round(nv(host, 'b', 164));
      a = Math.min(999, Math.max(0, a));
      b = Math.min(999, Math.max(0, b));
      var three = function (v) { return ('00' + v).slice(-3); };
      var prompt = three(a) + '+' + three(b) + '=';
      var got = greedy(M, prompt, 4);
      var plain = got.split('').reverse().join('');
      var want = ('000' + (a + b)).slice(-4);
      var lines = ['넣은 글자   ' + prompt,
        '모델이 쓴 것 ' + got + '   (일의 자리부터)',
        '뒤집으면   ' + plain,
        '실제 합    ' + want + '   ' + (plain === want ? '맞음' : '틀림')];
      api.w(host, api.esc(lines.join('\n')));
    });
  });
})();
