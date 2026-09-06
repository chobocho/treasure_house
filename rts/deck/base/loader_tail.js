
  root.__rts = { require: __req };
  // 덱의 데모 틀에 미니 RPG 를 등록한다. 등록만 하고 실행은 슬라이드가 열릴 때 한다 —
  // 1MB 짜리 문서에서 안 보는 데모까지 도는 것은 낭비다.
  if (root.__demo) {
    root.__demo('mini-rpg', function (host, api) {
      __req('web/minirpg').boot(host, api);
    });
  }
})(typeof window !== 'undefined' ? window : globalThis);
