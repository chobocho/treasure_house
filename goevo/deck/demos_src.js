// 이 덱의 데모 다섯 — 자료(DATA)는 위 한 줄에 gen_demos.py 가 붙인다.
// 외부 라이브러리 없이 순수 자바스크립트. 정답은 check_deck.js 의 CASES 가
// data/·out/ 의 표가 낸 값과 견준다(PLAN.md §3.6, §5 8단계).
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

// ── 1) 연표 훑기 — 해를 고르면 그해의 사건과 그해 말의 최신판 ─────────
// O(연표 행 수 + 릴리스 수)
__demo('timeline', function (host, api) {
  bind(host, function () {
    var y = parseInt(val(host, 'year', '2012'), 10);
    if (!(y >= 2007 && y <= 2027)) {
      api.w(host, '2007 ~ 2027 사이의 해를 넣으십시오', 'bad');
      return;
    }
    var end = y + '-12-31', latest = null;
    DATA.rel.forEach(function (r) { if (r[1] <= end) latest = r; });
    var lines = [latest
      ? '그해 말의 최신판  <span class="ok">Go ' + latest[0] + '</span> (' + latest[1] + ')'
      : '그해 말의 최신판  Go 1 이전'];
    DATA.tl.forEach(function (t) {
      if (t[0].slice(0, 4) === String(y)) lines.push(t[0] + '  ' + api.esc(t[1]));
    });
    if (lines.length === 1) lines.push('(연표에 이 해의 사건이 없습니다)');
    api.w(host, lines.join('\n'));
  });
});

// ── 2) 어느 판에서 왔을까? — 기능 목록에서 카드 한 장 ───────────────
// 카드 id 를 넣으면 그 카드, 비우면 '다른 카드' 단추가 무작위로 고른다.
__demo('whichver', function (host, api) {
  var pick = null;
  var next = host.querySelector('button');
  if (next) next.addEventListener('click', function () {
    pick = DATA.feat[Math.floor(Math.random() * DATA.feat.length)];
    var g = host.querySelector('[data-guess]');
    if (g) g.value = '';
  });
  bind(host, function () {
    var id = val(host, 'card', '');
    var card = pick;
    if (id) {
      card = null;
      DATA.feat.forEach(function (f) { if (f[0] === id) card = f; });
      if (!card) { api.w(host, '없는 카드: ' + api.esc(id), 'bad'); return; }
    }
    if (!card) card = DATA.feat[0];
    pick = card;
    var guess = val(host, 'guess', '');
    var out = '카드  ' + api.esc(card[2]) + '\n어느 판에서 왔을까요?';
    if (guess) {
      var hit = vcmp(guess.replace(/^go\s*/i, ''), card[1]) === 0;
      out += '\n' + (hit ? '<span class="ok">맞습니다</span>' : '<span class="bad">틀렸습니다</span>') +
        ' — Go ' + card[1] + ' · ' + link(api, card[3], card[3] ? '그 장으로' : '개관 표에만 있습니다');
    }
    api.w(host, out);
  });
});

// ── 3) go 줄 사다리 — go 1.N 을 고르면 어느 문법이 컴파일되나 ─────────
// 자료는 exps/p10 이 go 1.27.1 로 실제로 돌린 결과(out/ladder_data.txt).
__demo('ladder', function (host, api) {
  bind(host, function () {
    var v = val(host, 'go', '1.21').replace(/^go\s*/i, '');
    if (!/^1\.\d+$/.test(v)) { api.w(host, '1.N 꼴로 넣으십시오 (예: 1.21)', 'bad'); return; }
    var lines = ['go ' + v + ' 에서'];
    DATA.ladder.forEach(function (r) {
      var ok = vcmp(v, r[1]) >= 0;
      lines.push((ok ? '<span class="ok">✓</span> ' : '✗ ') + api.esc(r[2]) + ' (go ' + r[1] + ')');
    });
    api.w(host, lines.join('\n'));
  });
});

// ── 4) API 증가 — 판을 고르면 그 판에 더해진 API ─────────────────────
__demo('api', function (host, api) {
  bind(host, function () {
    var v = val(host, 'ver', '1.21').replace(/^go\s*/i, '');
    var row = null;
    DATA.api.forEach(function (a) { if (a[0] === v) row = a; });
    if (!row) { api.w(host, 'api/go' + api.esc(v) + '.txt 가 없습니다 (1.0 ~ 1.27)', 'bad'); return; }
    var out = 'Go ' + row[0] + '  새 패키지 <span class="ok">' + row[1] + '</span>개 · 새 기호 ' +
      row[2] + '개 (그 가운데 syscall ' + row[3] + '개)';
    if (row[4].length) out += '\n새 패키지 ' + api.esc(row[4].join(', ')) +
      (row[1] > row[4].length ? ' …' : '');
    api.w(host, out);
  });
});

// ── 5) GODEBUG 찾기 — 설정 이름(일부)을 넣으면 생긴 판과 기본값이 바뀐 판 ──
__demo('godebug', function (host, api) {
  bind(host, function () {
    var q = val(host, 'name', 'panicnil').toLowerCase();
    var hits = DATA.godebug.filter(function (g) { return g[0].indexOf(q) >= 0; });
    if (!hits.length) { api.w(host, '없는 설정: ' + api.esc(q) + ' — go 1.27.1 의 표에 없습니다', 'bad'); return; }
    var lines = hits.slice(0, 8).map(function (g) {
      var s = g[0] + ' (' + g[1] + ')  생긴 판 ' + g[2];
      if (g[3] !== '-') s += ' · 기본값이 바뀐 판 ' + g[3] + ' · 옛 값 ' + g[0] + '=' + g[4];
      return s;
    });
    if (hits.length > 8) lines.push('… 외 ' + (hits.length - 8) + '개 — 더 좁혀 보십시오');
    api.w(host, lines.join('\n'));
  });
});
