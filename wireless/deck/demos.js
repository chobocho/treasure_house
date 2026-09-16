/* 이 덱의 데모들 — 조립기가 tail.html 의 <!--DEMOS--> 자리에 넣는다.
 *
 * 규칙 셋.
 *   1. **파이썬 참조와 같은 식을 쓴다.** py/wirelesslib 가 진짜이고
 *      여기는 그것을 손으로 만져 보게 한 것이다. 식이 갈라지면
 *      deck/check_deck.js 의 CASES 가 잡는다 — 거기 적힌 기댓값은
 *      파이썬이 낸 값이지 이 스크립트가 낸 값이 아니다.
 *   2. **빈 입력에서 죽지 않는다.** 사용자가 처음 여는 순간이
 *      그 상태다. 숫자를 못 읽으면 기본값으로 간다.
 *   3. **처음 배선될 때 한 번 그린다.** 단추를 눌러야만 뭔가 나오면
 *      슬라이드를 넘긴 사람은 빈 상자만 본다.
 */
(function () {
  'use strict';

  /* ---- 수치 도구 ---------------------------------------------- */

  // erfc — 체비셰프 맞춤(수치 처방전). 배정도에서 사실상 정확하다.
  var COF = [
    -1.3026537197817094, 6.4196979235649026e-1, 1.9476473204185836e-2,
    -9.561514786808631e-3, -9.46595344482036e-4, 3.66839497852761e-4,
    4.2523324806907e-5, -2.0278578112534e-5, -1.624290004647e-6,
    1.303655835580e-6, 1.5626441722e-8, -8.5238095915e-8,
    6.529054439e-9, 5.059343495e-9, -9.91364156e-10, -2.27365122e-10,
    9.6467911e-11, 2.394038e-12, -6.886027e-12, 8.94487e-13,
    3.13092e-13, -1.12708e-13, 3.81e-16, 7.106e-15];
  function erfc(x) {
    var z = Math.abs(x), t = 2.0 / (2.0 + z), ty = 4.0 * t - 2.0;
    var d = 0.0, dd = 0.0, tmp, j;
    for (j = COF.length - 1; j > 0; j--) {
      tmp = d; d = ty * d - dd + COF[j]; dd = tmp;
    }
    var ans = t * Math.exp(-z * z + 0.5 * (COF[0] + ty * d) - dd);
    return x >= 0 ? ans : 2.0 - ans;
  }
  function Q(x) { return 0.5 * erfc(x / Math.SQRT2); }
  function db2lin(d) { return Math.pow(10.0, d / 10.0); }
  function log10(x) { return Math.log(x) / Math.LN10; }

  // 값 읽기 — 없거나 숫자가 아니면 기본값. 빈 입력에서 죽지 않는다.
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
  function f(x, n) {
    if (!isFinite(x)) return '—';
    return x.toFixed(n === undefined ? 2 : n);
  }
  function e2(x) {
    if (!isFinite(x) || x <= 0) return '0';
    return x.toExponential(2);
  }
  // 입력이 바뀌면 다시 그린다. 스텁에서는 목록이 비어 아무 일도 없다.
  function wire(host, draw) {
    var list = host.querySelectorAll('input, select, button');
    for (var i = 0; i < list.length; i++) {
      list[i].addEventListener('input', draw);
      list[i].addEventListener('change', draw);
      list[i].addEventListener('click', draw);
    }
    draw();
  }
  function bar(v, max, n) {
    var k = Math.max(0, Math.min(n, Math.round(v / max * n)));
    return new Array(k + 1).join('█') + new Array(n - k + 1).join('·');
  }

  /* ---- 1. BER 계산기 ------------------------------------------- */
  // 파이썬 modem.ber_theory 와 같은 식.
  var MOD = {
    bpsk: { k: 1, m: 2 }, qpsk: { k: 2, m: 4 },
    '16qam': { k: 4, m: 16 }, '64qam': { k: 6, m: 64 },
    '256qam': { k: 8, m: 256 }
  };
  function berTheory(name, ebn0Db) {
    var c = MOD[name] || MOD.bpsk, g = db2lin(ebn0Db);
    if (name === 'bpsk' || name === 'qpsk') return Q(Math.sqrt(2.0 * g));
    return (4.0 / c.k) * (1.0 - 1.0 / Math.sqrt(c.m))
      * Q(Math.sqrt(3.0 * c.k * g / (c.m - 1)));
  }
  window.__demo('d-ber', function (host, api) {
    wire(host, function () {
      var name = sv(host, 'mod', 'bpsk');
      var ebn0 = nv(host, 'ebn0', 10);
      var b = berTheory(name, ebn0);
      var lines = [];
      lines.push(name.toUpperCase() + ' · Eb/N0 ' + f(ebn0, 1)
        + ' dB → BER ' + e2(b));
      lines.push('비트 100만 개에 틀리는 비트 ' + f(b * 1e6, 1) + '개');
      lines.push('');
      var names = ['bpsk', 'qpsk', '16qam', '64qam'];
      for (var i = 0; i < names.length; i++) {
        lines.push(('        ' + names[i]).slice(-7) + '  '
          + e2(berTheory(names[i], ebn0)));
      }
      api.w(host, api.esc(lines.join('\n')));
    });
  });

  /* ---- 2. 성상도와 잡음 ---------------------------------------- */
  window.__demo('d-const', function (host, api) {
    wire(host, function () {
      var name = sv(host, 'mod', 'qpsk');
      var c = MOD[name] || MOD.qpsk;
      var side = Math.round(Math.sqrt(c.m));
      var ebn0 = nv(host, 'ebn0', 15);
      // 심벌당 SNR = Eb/N0 · k. 이웃 사이 거리 대비 잡음을 잰다.
      var esn0 = db2lin(ebn0) * c.k;
      var lines = [];
      lines.push(name.toUpperCase() + ' — 점 ' + c.m + '개 · 심벌당 '
        + c.k + '비트');
      lines.push('Es/N0 = ' + f(10.0 * log10(esn0), 2) + ' dB');
      if (name === 'bpsk' || name === 'qpsk') {
        lines.push('배치: 반지름 1 의 원 위에 고르게');
      } else {
        lines.push('배치: ' + side + '×' + side + ' 격자');
      }
      lines.push('BER(이론) = ' + e2(berTheory(name, ebn0)));
      lines.push('');
      lines.push('잡음 구름의 크기 ' + bar(1 / Math.sqrt(esn0), 1, 20));
      api.w(host, api.esc(lines.join('\n')));
    });
  });

  /* ---- 3. 경로손실 비교 ---------------------------------------- */
  // 파이썬 channel.fspl_db · log_distance_db · hata_db 와 같은 식.
  function fspl(dM, fHz) {
    return 20.0 * log10(4.0 * Math.PI * dM * fHz / 299792458.0);
  }
  function hataA(fMhz, hmM) {
    if (fMhz >= 400.0) {
      return 3.2 * Math.pow(log10(11.75 * hmM), 2) - 4.97;
    }
    return 8.29 * Math.pow(log10(1.54 * hmM), 2) - 1.1;
  }
  function hata(fMhz, hbM, hmM, dKm) {
    return 69.55 + 26.16 * log10(fMhz) - 13.82 * log10(hbM)
      - hataA(fMhz, hmM)
      + (44.9 - 6.55 * log10(hbM)) * log10(dKm);
  }
  window.__demo('d-pathloss', function (host, api) {
    wire(host, function () {
      var dKm = nv(host, 'dist', 1);
      var fMhz = nv(host, 'freq', 900);
      var n = nv(host, 'expo', 3.5);
      if (dKm <= 0) dKm = 1;
      if (fMhz <= 0) fMhz = 900;
      var dM = dKm * 1000.0, fHz = fMhz * 1e6;
      var lines = [];
      lines.push('거리 ' + f(dKm, 2) + ' km · ' + f(fMhz, 0) + ' MHz');
      lines.push('');
      lines.push('자유공간      ' + f(fspl(dM, fHz), 2) + ' dB');
      lines.push('로그거리 n=' + f(n, 1) + ' '
        + f(fspl(1.0, fHz) + 10.0 * n * log10(dM), 2) + ' dB');
      if (fMhz >= 150 && fMhz <= 1500 && dKm >= 1 && dKm <= 20) {
        lines.push('하타(대도시)  ' + f(hata(fMhz, 30, 1.5, dKm), 2)
          + ' dB');
      } else {
        lines.push('하타(대도시)  적용 범위 밖'
          + ' (150~1500 MHz · 1~20 km)');
      }
      api.w(host, api.esc(lines.join('\n')));
    });
  });

  /* ---- 4. 링크 버짓 -------------------------------------------- */
  // 파이썬 link.budget 과 같은 식. 상수도 같은 것을 쓴다.
  function noiseFloor(bwHz, nfDb) {
    return 10.0 * log10(1.380649e-23 * 290.0 * bwHz * 1000.0) + nfDb;
  }
  window.__demo('d-link', function (host, api) {
    wire(host, function () {
      var ptx = nv(host, 'ptx', 23);
      var grx = nv(host, 'grx', 18);
      var pl = nv(host, 'pl', 98.47);
      var bw = nv(host, 'bw', 10);
      var nf = nv(host, 'nf', 3);
      var req = nv(host, 'req', 10);
      if (bw <= 0) bw = 10;
      var prx = ptx - pl + grx;
      var nfl = noiseFloor(bw * 1e6, nf);
      var snr = prx - nfl;
      var lines = [];
      lines.push('EIRP          ' + f(ptx) + ' dBm');
      lines.push('경로손실      -' + f(pl) + ' dB');
      lines.push('수신 안테나   +' + f(grx) + ' dBi');
      lines.push('수신 전력     ' + f(prx) + ' dBm');
      lines.push('잡음 바닥     ' + f(nfl) + ' dBm');
      lines.push('SNR           ' + f(snr) + ' dB');
      lines.push('요구 SNR      ' + f(req) + ' dB');
      lines.push('여유          ' + f(snr - req) + ' dB');
      api.w(host, api.esc(lines.join('\n')));
    });
  });

  /* ---- 5. 육각 재사용과 SIR ------------------------------------ */
  // 파이썬 cellular.sir_db 와 같은 식.
  function sirDb(n, gamma, i0) {
    return 10.0 * log10(Math.pow(Math.sqrt(3.0 * n), gamma) / i0);
  }
  var CLUSTERS = [1, 3, 4, 7, 9, 12, 13, 16, 19, 21];
  window.__demo('d-reuse', function (host, api) {
    wire(host, function () {
      var n = Math.round(nv(host, 'cluster', 7));
      var gamma = nv(host, 'gamma', 4);
      var sect = Math.round(nv(host, 'sectors', 1));
      if (CLUSTERS.indexOf(n) < 0) n = 7;
      if (sect !== 1 && sect !== 3 && sect !== 6) sect = 1;
      var i0 = sect === 1 ? 6 : (sect === 3 ? 2 : 1);
      var lines = [];
      lines.push('N=' + n + ' · γ=' + f(gamma, 1) + ' · 섹터 ' + sect
        + '개 → 간섭원 ' + i0 + '개');
      lines.push('D/R = ' + f(Math.sqrt(3.0 * n), 3));
      lines.push('SIR = ' + f(sirDb(n, gamma, i0)) + ' dB');
      lines.push(sirDb(n, gamma, i0) >= 18
        ? 'AMPS 가 요구한 18 dB 를 넘는다' : '18 dB 에 못 미친다');
      lines.push('');
      for (var i = 0; i < CLUSTERS.length; i++) {
        var c = CLUSTERS[i];
        lines.push(('   N=' + c).slice(-5) + '  '
          + f(sirDb(c, gamma, i0)) + ' dB');
      }
      api.w(host, api.esc(lines.join('\n')));
    });
  });

  /* ---- 6. 얼랑 B ----------------------------------------------- */
  // 파이썬 cellular.erlang_b 와 같은 점화식 — 넘침이 없다.
  function erlangB(a, n) {
    var b = 1.0;
    for (var k = 1; k <= n; k++) b = a * b / (k + a * b);
    return b;
  }
  window.__demo('d-erlang', function (host, api) {
    wire(host, function () {
      var a = nv(host, 'load', 10);
      var n = Math.round(nv(host, 'lines', 15));
      if (a < 0) a = 10;
      if (n < 0 || n > 400) n = 15;
      var b = erlangB(a, n);
      var lines = [];
      lines.push('부하 ' + f(a, 2) + ' 얼랑 · 회선 ' + n + '개');
      lines.push('차단률 B = ' + f(b * 100, 3) + ' %');
      lines.push('실어 나르는 양 = ' + f(a * (1 - b), 3) + ' 얼랑');
      lines.push('회선당 효율 = ' + f(a * (1 - b) / (n || 1) * 100, 1)
        + ' %');
      lines.push('');
      lines.push('회선을 늘리면');
      for (var k = n; k <= n + 5; k++) {
        lines.push(('    ' + k).slice(-4) + '개  '
          + f(erlangB(a, k) * 100, 3) + ' %');
      }
      api.w(host, api.esc(lines.join('\n')));
    });
  });

  /* ---- 7. 왈시 확산 -------------------------------------------- */
  function walsh(n, k) {
    var row = [], i, j, bits, s;
    for (i = 0; i < n; i++) {
      bits = i & k; s = 0;
      for (j = 0; j < 16; j++) s ^= (bits >> j) & 1;
      row.push(s ? -1 : 1);
    }
    return row;
  }
  function pm(v) {
    return v.map(function (x) { return x > 0 ? '+' : '-'; }).join('');
  }
  window.__demo('d-walsh', function (host, api) {
    wire(host, function () {
      var n = Math.round(nv(host, 'sf', 8));
      var k = Math.round(nv(host, 'code', 3));
      var other = Math.round(nv(host, 'other', 5));
      if (n !== 4 && n !== 8 && n !== 16) n = 8;
      if (k < 0 || k >= n) k = 3 % n;
      if (other < 0 || other >= n) other = 5 % n;
      var a = walsh(n, k), b = walsh(n, other);
      var dot = 0, i;
      for (i = 0; i < n; i++) dot += a[i] * b[i];
      var self = 0;
      for (i = 0; i < n; i++) self += a[i] * a[i];
      var lines = [];
      lines.push('SF=' + n + ' · 처리 이득 ' + f(10.0 * log10(n)) + ' dB');
      lines.push('W' + k + '  ' + pm(a));
      lines.push('W' + other + '  ' + pm(b));
      lines.push('');
      lines.push('내 부호와의 내적   = ' + self + '  (신호가 모인다)');
      lines.push('남의 부호와의 내적 = ' + dot
        + (dot === 0 ? '  (직교 — 안 보인다)' : '  (직교가 아니다)'));
      api.w(host, api.esc(lines.join('\n')));
    });
  });

  /* ---- 8. 원근 문제 -------------------------------------------- */
  window.__demo('d-nearfar', function (host, api) {
    wire(host, function () {
      var far = nv(host, 'far', -40);
      var on = !!(host.querySelector('[data-pc]') || {}).checked;
      var sinr = on ? 0.0 : far;
      var lines = [];
      lines.push('먼 단말의 도착 세기 ' + f(far, 1)
        + ' dB (가까운 단말 기준)');
      lines.push('전력 제어 ' + (on ? '켬' : '끔'));
      lines.push('');
      lines.push('먼 단말이 보는 신호 대 간섭비 = ' + f(sinr, 1) + ' dB');
      lines.push(on
        ? '둘이 같은 세기로 도착해 대등하다'
        : '가까운 단말 하나가 셀을 묻어 버린다');
      lines.push('');
      lines.push('세기  ' + bar(sinr + 60, 60, 20));
      api.w(host, api.esc(lines.join('\n')));
    });
  });

  /* ---- 9. 부반송파 직교성 -------------------------------------- */
  window.__demo('d-ofdm', function (host, api) {
    wire(host, function () {
      var nfft = Math.round(nv(host, 'nfft', 16));
      var k1 = Math.round(nv(host, 'k1', 1));
      var k2 = Math.round(nv(host, 'k2', 3));
      var eps = nv(host, 'eps', 0);
      if (nfft < 4 || nfft > 256) nfft = 16;
      if (k1 < 0 || k1 >= nfft) k1 = 1;
      if (k2 < 0 || k2 >= nfft) k2 = 3;
      var re = 0, im = 0, i, ph;
      for (i = 0; i < nfft; i++) {
        ph = 2 * Math.PI * ((k1 + eps) - k2) * i / nfft;
        re += Math.cos(ph); im += Math.sin(ph);
      }
      var mag = Math.sqrt(re * re + im * im) / nfft;
      var ici = Math.pow(Math.PI * eps, 2) / 3.0;
      var lines = [];
      lines.push('FFT ' + nfft + '점 · 부반송파 ' + k1 + ' 와 ' + k2);
      lines.push('주파수 오차 ε = ' + f(eps, 3) + ' (부반송파 간격 대비)');
      lines.push('');
      lines.push('두 부반송파의 내적 크기 = ' + f(mag, 6));
      lines.push(mag < 1e-9
        ? '정확히 0 — 직교한다'
        : '0 이 아니다 — 직교가 깨졌다');
      lines.push('ICI 전력(근사 (πε)²/3) = ' + e2(ici));
      api.w(host, api.esc(lines.join('\n')));
    });
  });

  /* ---- 10. NR 뉴머롤로지 --------------------------------------- */
  window.__demo('d-numerology', function (host, api) {
    wire(host, function () {
      var mu = Math.round(nv(host, 'mu', 0));
      if (mu < 0 || mu > 6) mu = 0;
      var scs = 15 * Math.pow(2, mu);
      var sym = 1000.0 / scs;
      var slot = 1.0 / Math.pow(2, mu);
      var lines = [];
      lines.push('μ=' + mu + ' → SCS ' + scs + ' kHz');
      lines.push('유용 심볼 ' + f(sym, 2) + ' μs  (SCS × 심볼 = 1)');
      lines.push('슬롯 ' + f(slot, 5) + ' ms · 심볼 14개');
      lines.push('서브프레임당 슬롯 ' + Math.pow(2, mu) + '개');
      lines.push('PRB 폭 ' + (scs * 12) + ' kHz');
      lines.push('');
      for (var m = 0; m <= 4; m++) {
        lines.push('μ=' + m + '  SCS ' + ('    ' + (15 * Math.pow(2, m))
          ).slice(-4) + ' kHz  슬롯 '
          + f(1.0 / Math.pow(2, m), 5) + ' ms');
      }
      api.w(host, api.esc(lines.join('\n')));
    });
  });

  /* ---- 11. 저궤도 지연과 도플러 -------------------------------- */
  // 파이썬 orbit 모듈과 같은 상수·같은 식.
  var R_KM = 6371.0, MU_E = 3.986004418e14, C_KM_MS = 299.792458;
  function slantKm(altKm, elDeg) {
    var e = elDeg * Math.PI / 180.0, r = R_KM;
    var ratio = (r + altKm) / r;
    return r * (Math.sqrt(ratio * ratio - Math.pow(Math.cos(e), 2))
      - Math.sin(e));
  }
  function speedMs(altKm) {
    return Math.sqrt(MU_E / ((R_KM + altKm) * 1000.0));
  }
  function maxDopplerHz(altKm, fcHz) {
    var th = Math.acos(R_KM / (R_KM + altKm));
    var r = R_KM * 1000.0, a = (R_KM + altKm) * 1000.0;
    var w = speedMs(altKm) / a;
    var d = Math.sqrt(r * r + a * a - 2.0 * r * a * Math.cos(th));
    var rate = r * a * w * Math.sin(th) / d;
    return Math.abs(rate * fcHz / (C_KM_MS * 1e6));
  }
  window.__demo('d-orbit', function (host, api) {
    wire(host, function () {
      var alt = nv(host, 'alt', 550);
      var el = nv(host, 'elev', 90);
      var fGhz = nv(host, 'freq', 2);
      if (alt < 100 || alt > 40000) alt = 550;
      if (el < 0 || el > 90) el = 90;
      if (fGhz <= 0) fGhz = 2;
      var d = slantKm(alt, el);
      var oneWay = d / C_KM_MS;
      var dop = maxDopplerHz(alt, fGhz * 1e9);
      var lines = [];
      lines.push('고도 ' + f(alt, 0) + ' km · 앙각 ' + f(el, 0) + '°');
      lines.push('거리 ' + f(d, 1) + ' km');
      lines.push('편도 지연 ' + f(oneWay, 2) + ' ms · 왕복 '
        + f(2 * oneWay, 2) + ' ms');
      lines.push('궤도 속도 ' + f(speedMs(alt) / 1000.0, 3) + ' km/s');
      lines.push('');
      lines.push('최대 도플러(' + f(fGhz, 1) + ' GHz) = '
        + f(dop / 1000.0, 1) + ' kHz');
      lines.push('15 kHz 부반송파의 ' + f(dop / 15000.0, 2) + '배');
      api.w(host, api.esc(lines.join('\n')));
    });
  });

  /* ---- 12. 비터비 한 걸음씩 ------------------------------------ */
  // K=3, 생성 다항식 (7,5). 파이썬 codes.ConvCode 와 같은 규칙이다.
  function parity(x) {
    var s = 0;
    while (x) { s ^= x & 1; x >>= 1; }
    return s;
  }
  function convEncode(bits) {
    var out = [], st = 0, i, u, reg;
    var msg = bits.concat([0, 0]);
    for (i = 0; i < msg.length; i++) {
      u = msg[i] & 1;
      reg = (u << 2) | st;
      out.push(parity(reg & 7), parity(reg & 5));
      st = reg >> 1;
    }
    return out;
  }
  function viterbi(rx) {
    var NS = 4, INF = 1e9, steps = rx.length / 2;
    var m = [0, INF, INF, INF], back = [], i, st, u, reg, o0, o1, ns, c, nm;
    for (i = 0; i < steps; i++) {
      var nmv = [INF, INF, INF, INF], row = [0, 0, 0, 0];
      for (st = 0; st < NS; st++) {
        if (m[st] >= INF) continue;
        for (u = 0; u < 2; u++) {
          reg = (u << 2) | st;
          o0 = parity(reg & 7); o1 = parity(reg & 5);
          ns = reg >> 1;
          c = (o0 ^ rx[2 * i]) + (o1 ^ rx[2 * i + 1]);
          nm = m[st] + c;
          if (nm < nmv[ns]) { nmv[ns] = nm; row[ns] = st * 2 + u; }
        }
      }
      m = nmv; back.push(row);
    }
    var best = 0;
    for (st = 1; st < NS; st++) if (m[st] < m[best]) best = st;
    var bits = [];
    for (i = steps - 1; i >= 0; i--) {
      var v = back[i][best];
      bits.unshift(v & 1);
      best = v >> 1;
    }
    return { bits: bits.slice(0, steps - 2), metric: m[0] };
  }
  window.__demo('d-viterbi', function (host, api) {
    wire(host, function () {
      var s = sv(host, 'msg', '10110').replace(/[^01]/g, '');
      if (!s) s = '10110';
      if (s.length > 10) s = s.slice(0, 10);
      var msg = s.split('').map(Number);
      var enc = convEncode(msg);
      var flip = Math.round(nv(host, 'flip', -1));
      var rx = enc.slice();
      if (flip >= 0 && flip < rx.length) rx[flip] ^= 1;
      var dec = viterbi(rx);
      var lines = [];
      lines.push('메시지   ' + msg.join(''));
      lines.push('부호화   ' + enc.join('') + '   (r=1/2, K=3, 꼬리 2)');
      lines.push('받은 것  ' + rx.join('')
        + (flip >= 0 && flip < enc.length ? '   ← ' + flip
          + '번 비트를 뒤집었다' : ''));
      lines.push('복호     ' + dec.bits.join(''));
      lines.push('');
      lines.push(dec.bits.join('') === msg.join('')
        ? '원래 메시지를 되찾았다' : '되찾지 못했다');
      api.w(host, api.esc(lines.join('\n')));
    });
  });
})();
