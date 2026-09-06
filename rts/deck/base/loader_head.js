/* ============================================================
   28부의 타입스크립트 엔진을 브라우저에서 그대로 돌리기 위한 묶음.

   이 파일의 코드는 ts/src/*.ts 를 tsc 가 옮긴 것이고, 손으로 고친 곳이 없다.
   그래서 이 문서 안에서 움직이는 유닛의 좌표는 golden/trace.jsonl 을 만든 것과
   같은 코드가 계산한 값이다. tools/check_web.js 가 매번 그것을 대조한다.

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
    // 이 구분을 빠뜨리면 경로탐색 모듈이 경로 스텁으로 가려진다.
    var builtin = raw.charAt(0) !== '.';
    if (builtin && n === 'path') {
      // join 만 진짜로 만든다. resolve 와 dirname 은 브라우저에서 쓸 일이 없고,
      // 그럴듯한 값을 돌려주면 나중에 누가 쓸 때 조용히 틀린 경로가 흘러다닌다.
      var join = function () { return Array.prototype.join.call(arguments, '/'); };
      var nope = function (what) {
        return function () { throw new Error('브라우저에서는 path.' + what + ' 를 쓸 수 없다'); };
      };
      return { join: join, resolve: join, dirname: nope('dirname'),
               basename: nope('basename'), relative: nope('relative') };
    }
    if (builtin && n === 'fs') {
      // 브라우저에는 파일이 없다. 조용히 빈 값을 돌려주면 맵이 비고 시나리오가
      // 사라진 채로 게임이 도는데, 그 화면은 "그럴듯해" 보인다. 그래서 터뜨린다.
      return { readFileSync: function () {
        throw new Error('브라우저에서는 파일을 읽을 수 없다 — web/data.ts 의 문자열을 쓸 것');
      }, writeFileSync: function () { throw new Error('브라우저에서는 파일을 쓸 수 없다'); } };
    }
    if (__cache[n]) return __cache[n];
    var f = __mods[n] || __mods['web/' + n];
    if (!f) throw new Error('모듈 없음: ' + name);
    var m = { exports: {} };
    // 순환 참조를 위해 평가 전에 미리 넣는다. 대신 평가가 터지면 반드시 걷어낸다 —
    // 안 그러면 다음 require 가 반쯤 만들어진 exports 를 조용히 돌려준다.
    __cache[n] = m.exports;
    try {
      // tsc 가 낸 코드에 __dirname 이 남아 있을 수 있다(경로 상수). 브라우저에는
      // 그런 전역이 없으므로 여기서 넣어 준다. 값은 쓰이지 않는다.
      f(m.exports, __req, m, '/');
    } catch (e) {
      delete __cache[n];
      throw e;
    }
    __cache[n] = m.exports;
    return m.exports;
  }
