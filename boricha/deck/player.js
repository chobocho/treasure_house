// player.js — 덱 안에서 터미널 기록을 넘겨 보는 재생기. 의존성 0.
//
// 기록은 tools/record 가 뽑고 tools/ansi2html 이 HTML 로 바꾼 것이다.
// 각 프레임은 "앞 프레임과 달라진 줄"만 갖고 있으므로, 여기서 줄 배열을 하나 들고
// 차례로 덧칠해 나간다. 뒤로 갈 때는 0번부터 다시 칠한다 — 프레임이 수십 장뿐이라
// 그게 가장 단순하고 충분히 빠르다.
//
// 슬라이드 넘김(←/→)과 겹치지 않게, 키는 [ 와 ] 를 쓰고 버튼도 함께 둔다.
(function () {
  'use strict';

  var DATA = window.__FRAMES || {};

  // 클래스 표를 <style> 하나로 만들어 문서에 올린다. 기록마다 이름이 겹치지 않게
  // 접두사를 붙인다 — 두 기록이 같은 'a0' 을 다른 색으로 쓸 수 있기 때문이다.
  function injectStyles() {
    var css = [];
    Object.keys(DATA).forEach(function (name) {
      var st = DATA[name].styles || {};
      Object.keys(st).forEach(function (cls) {
        css.push('.pl-' + name + ' .' + cls + '{' + st[cls] + '}');
      });
    });
    if (!css.length) return;
    var el = document.createElement('style');
    el.textContent = css.join('\n');
    document.head.appendChild(el);
  }

  // 0번부터 n번까지 덧칠해 화면 한 장을 만든다.
  function frameAt(rec, n) {
    var lines = [];
    for (var i = 0; i <= n && i < rec.frames.length; i++) {
      var f = rec.frames[i];
      (f.d || []).forEach(function (d) { lines[d[0]] = d[1]; });
      lines.length = f.n;
    }
    for (var y = 0; y < lines.length; y++) if (lines[y] === undefined) lines[y] = '';
    return lines.join('\n');
  }

  function mount(host) {
    var name = host.dataset.frames;
    var rec = DATA[name];
    if (!rec) { host.innerHTML = '<div class="warn">기록 ' + name + ' 이 없습니다</div>'; return; }

    host.classList.add('pl-' + name);
    host.innerHTML =
      '<div class="plbar">' +
        '<button class="plprev" aria-label="이전 프레임">◀</button>' +
        '<input class="plrange" type="range" min="0" max="' + (rec.frames.length - 1) + '" value="0">' +
        '<button class="plnext" aria-label="다음 프레임">▶</button>' +
        '<button class="plplay" aria-label="자동 재생">▶︎ 재생</button>' +
        '<span class="plnow"></span>' +
      '</div>' +
      '<pre class="plscreen"></pre>';

    var screen = host.querySelector('.plscreen');
    var range = host.querySelector('.plrange');
    var now = host.querySelector('.plnow');
    var play = host.querySelector('.plplay');
    var at = 0, timer = null;

    function draw() {
      screen.innerHTML = frameAt(rec, at);
      range.value = at;
      now.textContent = (at + 1) + ' / ' + rec.frames.length +
        ' · ' + (rec.frames[at].label || '');
    }
    function go(n) {
      at = Math.max(0, Math.min(rec.frames.length - 1, n));
      draw();
    }
    function stop() {
      if (timer) clearInterval(timer);
      timer = null;
      play.textContent = '▶︎ 재생';
    }
    function toggle() {
      if (timer) { stop(); return; }
      if (at >= rec.frames.length - 1) at = 0;
      play.textContent = '❚❚ 멈춤';
      timer = setInterval(function () {
        if (at >= rec.frames.length - 1) { stop(); return; }
        go(at + 1);
      }, 420);
    }

    host.querySelector('.plprev').onclick = function () { stop(); go(at - 1); };
    host.querySelector('.plnext').onclick = function () { stop(); go(at + 1); };
    play.onclick = toggle;
    range.oninput = function () { stop(); go(+range.value); };

    // 키는 [ 와 ] — 슬라이드 넘김(←/→)과 겹치지 않게.
    host.tabIndex = 0;
    host.addEventListener('keydown', function (e) {
      if (e.key === '[') { stop(); go(at - 1); e.preventDefault(); }
      if (e.key === ']') { stop(); go(at + 1); e.preventDefault(); }
    });

    draw();
  }

  function mountAll() {
    injectStyles();
    var hosts = document.querySelectorAll('.player[data-frames]');
    for (var i = 0; i < hosts.length; i++) mount(hosts[i]);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', mountAll);
  } else {
    mountAll();
  }

  // 덱 점검 도구가 부를 수 있게 열어 둔다.
  window.__player = { frameAt: frameAt, data: DATA };
})();
