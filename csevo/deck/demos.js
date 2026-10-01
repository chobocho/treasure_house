"use strict";
// 생성 파일 — deck/gen_demos.py 가 data/·out/ 의 표와 deck/demos_src.js 로 만든다.
// 손으로 고치지 말 것. 데모 코드는 demos_src.js 에서 고친다.
var DATA = {};
// 이 덱의 데모 — 자료(DATA)는 위 한 줄에 gen_demos.py 가 붙인다.
// 외부 라이브러리 없이 순수 자바스크립트. 정답은 check_deck.js 의 CASES 가
// data/·out/ 의 표가 낸 값과 견준다(PLAN.md §4 7단계).
//
// 입력칸은 data-<이름> 으로 표시한다. check_deck.js 의 DOM 스텁이 그
// 모양을 보고 값을 넣어 주므로, 모양을 바꾸면 검사가 기본값만 보게 된다.

function val(host, name, dflt) {
  var el = host.querySelector('[data-' + name + ']');
  var v = el && el.value;
  return (v === undefined || v === null || v === '') ? dflt : String(v).trim();
}
function bind(host, run) {
  var bs = host.querySelectorAll('button');
  for (var i = 0; i < bs.length; i++) bs[i].addEventListener('click', run);
  var ins = host.querySelectorAll('input, select');
  for (i = 0; i < ins.length; i++) {
    ins[i].addEventListener('input', run);
    ins[i].addEventListener('change', run);
  }
  run();
}
// '1.9' < '1.10' — 판은 글자가 아니라 수로 견준다
function vcmp(a, b) {
  var x = a.split('.'), y = b.split('.');
  for (var i = 0; i < Math.max(x.length, y.length); i++) {
    var d = (+x[i] || 0) - (+y[i] || 0);
    if (d) return d;
  }
  return 0;
}
function link(api, sid, text) {
  return sid ? '<a href="#' + sid + '">' + api.esc(text) + '</a>' : api.esc(text);
}

// 데모 함수는 7단계(PLAN.md §4)에서 goevo/deck/demos_src.js 를 본떠 더한다.
