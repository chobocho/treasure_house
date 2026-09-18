/* 이 덱의 데모들 — 조립기가 tail.html 의 <!--DEMOS--> 자리에 넣는다.
 * (transformer/deck/demos.js 의 규칙을 물려받았다.)
 *
 *   1. 규칙은 같은 장에 실린 upstream 소스 발췌를 그대로 옮긴다. 옮긴
 *      것이 어긋나면 deck/check_deck.js 의 CASES 가 잡는다 — 거기 적힌
 *      기댓값은 소스의 규칙과 out/ 의 캡처에서 온 값이다.
 *   2. 빈 입력에서 죽지 않는다. 못 읽으면 기본값으로 간다.
 *   3. 처음 배선될 때 한 번 그린다.
 */
(function () {
  'use strict';

  var PREFIX = '/data/data/com.termux/files/usr';

  function sv(host, key, dflt) {
    var e = host.querySelector('[data-' + key + ']');
    if (!e || e.value === undefined || e.value === '') return dflt;
    return String(e.value);
  }
  function esc(s) {
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');
  }
  function wire(host, draw) {
    var list = host.querySelectorAll ?
      host.querySelectorAll('input, select, button') : [];
    for (var i = 0; i < list.length; i++) {
      list[i].addEventListener('input', draw);
      list[i].addEventListener('change', draw);
    }
    draw();
  }

  /* ---- 1. termux-exec 경로 번역기 (5부) ----
   * TermuxFile.c 301–341 을 옮긴 것:
   *   상대 경로 → 그대로
   *   "/bin" · "/usr/bin" 자체 → $PREFIX/bin
   *   "/bin/" 이 맨 앞(0)이나 네 번째 글자(4)에서 시작 → $PREFIX/bin/ + 나머지
   *   그 밖 → 그대로
   * 4 는 "/usr/bin/" 처럼 세 글자 디렉터리 하나 아래라는 뜻이다 — 그래서
   * "/system/bin/sh" 는 바뀌지 않는다. */
  function termuxPath(p) {
    if (p.charAt(0) !== '/') return p;
    if (p === '/bin' || p === '/usr/bin') return PREFIX + '/bin';
    var k = p.indexOf('/bin/');
    if (k === 0 || k === 4) return PREFIX + '/bin/' + p.slice(k + 5);
    return p;
  }
  window.__demo('d-prefix', function (host, api) {
    function draw() {
      var p = sv(host, 'path', '/usr/bin/python');
      var q = termuxPath(p);
      api.w(host, esc(p) + '\n→ ' + esc(q) +
        (q === p ? '\n(바뀌지 않는다)' : '\n(termux-exec 가 바꾼다)'));
    }
    wire(host, draw);
  });

  /* ---- 2. pkg 하위 명령 해석기 (6부) ----
   * pkg.in 409–425 의 apt 갈래를 위에서부터 차례로 — case 는 처음 맞는
   * 줄에서 멈춘다. 끝의 * 는 "이것으로 시작하면" 이다. */
  var PKG = [
    [['f*'], 'dpkg -L'],
    [['sh*', 'inf*'], 'apt show'],
    [['add', 'i*'], '(미러 고르기) (필요하면 apt update) apt install'],
    [['autoc*'], 'apt autoclean'],
    [['cl*'], 'apt clean'],
    [['list-a*'], 'apt list'],
    [['list-i*'], 'apt list --installed'],
    [['rei*'], 'apt install --reinstall'],
    [['se*'], '(미러 고르기) (필요하면 apt update) apt search'],
    [['un*', 'rem*', 'rm', 'del*'], 'apt remove'],
    [['upd*'], '(미러 고르기) apt update'],
    [['up', 'upg*'], '(미러 고르기) apt update; apt full-upgrade']
  ];
  function match(pat, s) {
    if (pat.charAt(pat.length - 1) === '*') {
      return s.indexOf(pat.slice(0, -1)) === 0;
    }
    return s === pat;
  }
  function pkgToApt(cmd) {
    for (var i = 0; i < PKG.length; i++) {
      for (var j = 0; j < PKG[i][0].length; j++) {
        if (match(PKG[i][0][j], cmd)) {
          return { line: 412 + i, pat: PKG[i][0][j], apt: PKG[i][1] };
        }
      }
    }
    return null;
  }
  window.__demo('d-pkg', function (host, api) {
    function draw() {
      var c = sv(host, 'cmd', 'in');
      var r = pkgToApt(c);
      api.w(host, r ? 'pkg ' + esc(c) + '\n→ ' + esc(r.apt) +
        '\n(' + r.line + '행의 ' + esc(r.pat) + ' 에 맞는다)' :
        'pkg ' + esc(c) + '\n→ 모르는 명령(ERROR=true)');
    }
    wire(host, draw);
  });

  /* ---- 3. 팬텀 프로세스 계산기 (8부) ----
   * 한도 32 는 README NOTICE 와 Android-Docs 가 적은 기본값이다. 한도를
   * 넘으면 부모 앱의 oom adj 가 높은 쪽·오래된 쪽부터 죽인다. */
  var LIMIT = 32;
  window.__demo('d-phantom', function (host, api) {
    function draw() {
      var n = parseInt(sv(host, 'procs', '16'), 10);
      if (!isFinite(n) || n < 0) n = 0;
      var over = n - LIMIT;
      api.w(host, '팬텀 프로세스 ' + n + '개 · 한도 ' + LIMIT + '\n' +
        (over > 0 ? '→ ' + over + '개가 죽을 수 있다(오래된 것부터)' :
         '→ 한도까지 ' + (LIMIT - n) + '개 남음'));
    }
    wire(host, draw);
  });
})();
