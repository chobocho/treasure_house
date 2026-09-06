/* ============================================================
   16부의 타입스크립트 엔진을 브라우저에서 그대로 돌리기 위한 묶음.

   이 파일의 코드는 ts/src/*.ts 를 tsc 가 옮긴 것이고, 손으로 고친 곳이 없다.
   그래서 이 문서 안에서 걸어 다니는 캐릭터의 좌표는 golden/trace.jsonl 을
   만든 것과 같은 코드가 계산한 값이다.

   tools/bundle_web.py 가 만든다. 손으로 고치지 말 것.
   ============================================================ */
(function (root) {
  'use strict';
  var __mods = {};
  var __cache = {};
  function __def(name, fn) { __mods[name] = fn; }
  function __req(name) {
    var raw = String(name);
    // './fixed' 나 '../raster' 같은 상대 경로를 이름으로 되돌린다.
    var n = raw.replace(/^(\.\.?\/)+/, '').replace(/\.js$/, '');
    // 점으로 시작하지 않으면 노드 내장 모듈이다. 엔진에도 path 라는 모듈이 있어서
    // 이 구분을 빠뜨리면 game.ts 가 경로 스텁을 경로탐색 모듈로 착각한다.
    var builtin = raw.charAt(0) !== '.';
    if (builtin && n === 'path') {
      // 경로 계산은 모듈을 불러올 때 바로 돈다(raster.ts 의 ROOT 상수).
      // 값을 쓰지는 않으므로 문자열만 이어 준다.
      var join = function () { return Array.prototype.join.call(arguments, '/'); };
      return { join: join, resolve: join, dirname: function (q) { return String(q); } };
    }
    if (builtin && n === 'fs') {
      // 브라우저에는 파일이 없다. 조용히 넘어가지 않고 터지게 둔다.
      return { readFileSync: function () {
        throw new Error('브라우저에서는 파일을 읽을 수 없다 — parsePalette / parseSprites / runScriptText 를 쓸 것');
      }, writeFileSync: function () { throw new Error('브라우저에서는 파일을 쓸 수 없다'); } };
    }
    if (__cache[n]) return __cache[n];
    var f = __mods[n] || __mods['web/' + n];
    if (!f) throw new Error('모듈 없음: ' + name);
    var m = { exports: {} };
    __cache[n] = m.exports;
    f(m.exports, __req, m);
    __cache[n] = m.exports;
    return m.exports;
  }
