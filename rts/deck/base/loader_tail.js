
  // names 는 검사 도구용이다 — tools/check_web.js 가 27개를 전부 평가해 보고
  // 브라우저에서만 터지는 최상위 코드(__dirname·process)가 없는지 확인한다.
  root.__rts = { require: __req, names: Object.keys(__mods) };
  // 덱의 데모 틀에 미니 RTS 를 등록한다. 등록만 하고 실행은 슬라이드가 열릴 때 한다 —
  // 1MB 짜리 문서에서 안 보는 판까지 도는 것은 낭비다.
  if (root.__demo) {
    root.__demo('mini-rts', function (host, api) {
      __req('web/minirts').boot(host, api);
    });
  }
})(typeof window !== 'undefined' ? window : globalThis);
