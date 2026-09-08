/* 이 덱의 브라우저 안 데모들.
 *
 * 규칙 셋:
 *   1) 바깥에서 아무것도 안 받아 온다. 계산은 전부 이 안에서 한다.
 *   2) 화면 조각이 없어도 죽지 않는다 — deck/check_deck.js 가 가짜 DOM 위에서
 *      전부 한 번씩 돌려 보기 때문이다. 죽으면 조립이 실패한다.
 *   3) 답을 그냥 보여 주지 않고, 사용자가 값을 바꿔 볼 수 있게 한다.
 *      "쿠키가 왜 안 붙지" 는 읽어서가 아니라 만져 봐야 안다.
 */
(function () {
  'use strict';

  // 화면 조각 찾기. 없으면 null 을 돌려주고, 부르는 쪽이 알아서 비켜 간다.
  function q(host, sel) {
    return host && host.querySelector ? host.querySelector(sel) : null;
  }
  function val(el, dflt) {
    if (!el) return dflt === undefined ? '' : dflt;
    var v = el.value;
    return v === undefined || v === null || v === '' ? (dflt || '') : v;
  }
  function on(el, ev, fn) {
    if (el && el.addEventListener) el.addEventListener(ev, fn);
  }

  /* ── 1. HTTP 요청 조립기 ────────────────────────────────────────
   * 방법·주소·헤더를 고르면 진짜로 나갈 바이트를 그대로 보여 준다.
   * 줄 끝이 CRLF 라는 것과, 헤더가 끝나면 빈 줄이 온다는 것이 요점이다. */
  __demo('http-builder', function (host, api) {
    var mEl = q(host, '[data-method]');
    var pEl = q(host, '[data-path]');
    var hEl = q(host, '[data-host]');
    var bEl = q(host, '[data-body]');

    function run() {
      var m = val(mEl, 'GET');
      var p = val(pEl, '/me');
      var h = val(hEl, 'lunch.campus.example');
      var b = val(bEl, '');
      var lines = [m + ' ' + p + ' HTTP/1.1', 'Host: ' + h,
        'User-Agent: deck-demo/1.0', 'Accept: */*'];
      if (m === 'POST') {
        lines.push('Content-Type: application/x-www-form-urlencoded');
        lines.push('Content-Length: ' + b.length);
      }
      var raw = lines.join('\r\n') + '\r\n\r\n' + (m === 'POST' ? b : '');
      // 눈에 안 보이는 것을 보이게 만든다 — 이게 이 데모의 전부다.
      // 표시 기호는 내장 글꼴(D2Coding)에 있는 것만 쓴다. ␍␊(제어 그림) 은
      // 그 글꼴에 없어서 다른 글꼴로 떨어지고, 그러면 칸이 어긋난다.
      var shown = raw.replace(/\r\n/g, '↵\n');
      api.w(host, api.esc(shown) +
        '\n\n<span class="dim">모두 ' + raw.length + '바이트' +
        (m === 'POST' ? '' : ' · 빈 줄까지가 요청의 끝') + '</span>');
    }
    on(mEl, 'change', run); on(pEl, 'input', run);
    on(hEl, 'input', run); on(bEl, 'input', run);
    run();
  });

  /* ── 2. 상태 번호 찾아보기 ──────────────────────────────────────
   * 백 자리만 보면 절반은 안다는 것을 손으로 확인하게 한다. */
  var STATUS = {
    200: ['OK', '됐다'],
    201: ['Created', '만들었다'],
    204: ['No Content', '됐는데 보여 줄 내용은 없다'],
    301: ['Moved Permanently', '아주 옮겼다. 브라우저가 기억한다'],
    302: ['Found', '지금만 저기다'],
    303: ['See Other', '결과는 저기 있으니 GET 으로 가라'],
    304: ['Not Modified', '안 바뀌었으니 갖고 있던 걸 써라'],
    307: ['Temporary Redirect', '302 인데 방법·본문 그대로'],
    308: ['Permanent Redirect', '301 인데 방법·본문 그대로'],
    400: ['Bad Request', '말이 안 되는 요청이다'],
    401: ['Unauthorized', '누군지 모르겠다 — 로그인해라'],
    403: ['Forbidden', '누군지는 알겠는데 안 된다'],
    404: ['Not Found', '그런 것 없다'],
    405: ['Method Not Allowed', '그 방법으로는 안 된다'],
    500: ['Internal Server Error', '서버가 터졌다'],
    502: ['Bad Gateway', '앞의 서버가 뒤에서 이상한 답을 받았다'],
    503: ['Service Unavailable', '지금은 못 받는다'],
    504: ['Gateway Timeout', '뒤가 대답을 안 한다']
  };
  var CLASSES = {
    1: '알림 — 아직 진행 중',
    2: '됐다',
    3: '다른 데를 봐라',
    4: '네가 잘못했다',
    5: '내가 잘못했다'
  };
  __demo('status', function (host, api) {
    var el = q(host, '[data-code]');
    function run() {
      var s = val(el, '401');
      var n = parseInt(s, 10);
      if (!(n >= 100 && n <= 599)) {
        api.w(host, '100~599 사이의 번호를 넣어 보세요.', 'dim');
        return;
      }
      var cls = CLASSES[Math.floor(n / 100)];
      var known = STATUS[n];
      var out = n + ' — 백 자리 ' + Math.floor(n / 100) + 'xx: ' +
        api.esc(cls);
      if (known) {
        out += '\n' + n + ' ' + api.esc(known[0]) + '\n  ' +
          api.esc(known[1]);
        api.w(host, out, 'ok');
      } else {
        out += '\n(이 덱에서 다루지 않는 번호다. 백 자리 뜻은 위와 같다)';
        api.w(host, out, 'dim');
      }
    }
    on(el, 'input', run);
    run();
  });

  /* ── 3. 리다이렉트 사슬 ─────────────────────────────────────────
   * 한 번에 한 칸씩 짚어 준다. 4부의 로그인 흐름이 이 사슬의 확장판이다. */
  var CHAIN = [
    ['GET /start', '302 Found', 'Location: /step2'],
    ['GET /step2', '302 Found', 'Location: /step3'],
    ['GET /step3', '200 OK', '(Location 없음 — 여기가 끝)']
  ];
  __demo('redirect', function (host, api) {
    var i = 0;
    function draw() {
      var out = [];
      for (var k = 0; k < CHAIN.length; k++) {
        var mark = k < i ? '  ' : (k === i ? '▶ ' : '  ');
        var c = CHAIN[k];
        var line = mark + c[0] + '  →  ' + c[1] + '   ' + c[2];
        out.push(k === i ? '<span class="ok">' + api.esc(line) + '</span>'
          : (k < i ? '<span class="dim">' + api.esc(line) + '</span>'
            : api.esc(line)));
      }
      var tail = i >= CHAIN.length - 1
        ? '\n브라우저는 이 셋을 사용자에게 묻지 않고 알아서 다 밟았다.'
        : '\n다음을 누르면 브라우저가 Location 을 따라간다.';
      api.w(host, out.join('\n') + '\n' + api.esc(tail));
    }
    on(q(host, '[data-next]'), 'click', function () {
      i = (i + 1) % CHAIN.length; draw();
    });
    on(q(host, '[data-reset]'), 'click', function () { i = 0; draw(); });
    draw();
  });

  /* ── 4. 쿠키가 붙는가 ───────────────────────────────────────────
   * 쿠키 사고의 열에 아홉은 Path·Domain·Secure 셋 중 하나다.
   * 규칙을 외우게 하지 말고 여기서 틀려 보게 한다. */
  __demo('cookie', function (host, api) {
    var pEl = q(host, '[data-cpath]');
    var sEl = q(host, '[data-secure]');
    var uEl = q(host, '[data-url]');

    function run() {
      var cpath = val(pEl, '/');
      var secure = !!(sEl && sEl.checked);
      var url = val(uEl, 'https://lunch.campus.example/me');
      var m = /^(https?):\/\/([^/]+)(\/[^?#]*)?/.exec(url);
      if (!m) {
        api.w(host, '주소를 http(s)://호스트/경로 꼴로 써 보세요.', 'bad');
        return;
      }
      var scheme = m[1], path = m[3] || '/';
      var reasons = [];
      // Path 규칙: 쿠키의 Path 이거나 그 아래여야 한다(RFC 6265 §5.1.4)
      var pathOK = path === cpath ||
        path.indexOf(cpath.replace(/\/$/, '') + '/') === 0 ||
        cpath === '/';
      if (!pathOK) reasons.push('Path=' + cpath + ' 아래가 아니다');
      if (secure && scheme !== 'https') reasons.push('Secure 인데 http 다');
      if (reasons.length) {
        api.w(host, '붙지 않는다 — ' + api.esc(reasons.join(' · ')), 'bad');
      } else {
        api.w(host, '붙는다 — Cookie: lunch_session=…', 'ok');
      }
    }
    on(pEl, 'input', run); on(sEl, 'change', run); on(uEl, 'input', run);
    run();
  });

  /* ── 5. base64 와 base64url ─────────────────────────────────────
   * 4부의 토큰이 왜 그 모양인지가 여기서 갈린다. */
  function toB64(s) {
    var bytes = new TextEncoder().encode(s);
    var bin = '';
    for (var i = 0; i < bytes.length; i++) bin += String.fromCharCode(bytes[i]);
    return btoa(bin);
  }
  __demo('base64', function (host, api) {
    var el = q(host, '[data-text]');
    function run() {
      var s = val(el, '민지:Passw0rd!-demo');
      var b64;
      try {
        b64 = toB64(s);
      } catch (e) {
        api.w(host, '바꿀 수 없는 글자가 있습니다.', 'bad');
        return;
      }
      // base64url = + 를 - 로, / 를 _ 로, 끝의 = 를 뗀 것 (RFC 4648 §5)
      var url = b64.replace(/\+/g, '-').replace(/\//g, '_')
        .replace(/=+$/, '');
      var note = b64 === url
        ? '이 값에는 + / = 가 없어서 둘이 같다.'
        : '+ → -, / → _, 끝의 = 를 뗐다. 주소에 그대로 실으려면 그래야 한다.';
      api.w(host,
        '<span class="dim">글자 ' + s.length + '개 · ' +
        new TextEncoder().encode(s).length + '바이트</span>\n' +
        'base64    ' + api.esc(b64) + '\n' +
        'base64url ' + api.esc(url) + '\n\n' +
        '<span class="dim">' + api.esc(note) + '</span>');
    }
    on(el, 'input', run);
    run();
  });

  /* ── 6. SHA-256 ─────────────────────────────────────────────────
   * 브라우저에 이미 들어 있는 Web Crypto 로 진짜 해시를 낸다.
   * 한 글자만 바꿔도 전부 달라진다는 것을 눈으로 보는 자리다. */
  __demo('hash', function (host, api) {
    var el = q(host, '[data-text]');
    function run() {
      var s = val(el, 'minji');
      var subtle = (window.crypto && window.crypto.subtle) || null;
      if (!subtle) {
        api.w(host, '이 브라우저에서는 계산할 수 없습니다 ' +
          '(https 로 열어야 Web Crypto 가 켜집니다).', 'dim');
        return;
      }
      subtle.digest('SHA-256', new TextEncoder().encode(s)).then(function (b) {
        var v = new Uint8Array(b), hex = '';
        for (var i = 0; i < v.length; i++) {
          hex += (v[i] < 16 ? '0' : '') + v[i].toString(16);
        }
        api.w(host, api.esc(s) + '\n  → ' + hex.slice(0, 32) + '\n    ' +
          hex.slice(32) + '\n\n<span class="dim">언제 계산해도 같은 값이고, ' +
          '한 글자만 바꾸면 전부 달라진다.</span>', 'ok');
      }).catch(function (e) {
        api.w(host, '계산 실패: ' + api.esc(e.message), 'bad');
      });
    }
    on(el, 'input', run);
    run();
  });

  /* ── 8. LDAP 필터 해석기 ────────────────────────────────────────
   * 3부에서 만든 가짜 AD 와 **같은 자료**를 담아 두고, 친 필터가 누구를
   * 고르는지 바로 보여 준다. 필터는 외워지지 않는다 — 틀려 봐야 는다. */
  var DIR = [
    { dn: 'CN=Kim Minji,OU=Students', cn: 'Kim Minji', sn: 'Kim',
      samaccountname: 'minji', mail: 'minji@campus.example',
      objectclass: 'top person organizationalPerson user',
      useraccountcontrol: '512',
      memberof: 'CN=lunch-users,OU=Groups CN=campus-all,OU=Groups' },
    { dn: 'CN=Kim Junho,OU=Staff', cn: 'Kim Junho', sn: 'Kim',
      samaccountname: 'prof.kim', mail: 'prof.kim@campus.example',
      objectclass: 'top person organizationalPerson user',
      useraccountcontrol: '66048',
      memberof: 'CN=lunch-users,OU=Groups CN=campus-all,OU=Groups' },
    { dn: 'CN=Lee Sohee,OU=Staff', cn: 'Lee Sohee', sn: 'Lee',
      samaccountname: 'admin.lee', mail: 'admin.lee@campus.example',
      objectclass: 'top person organizationalPerson user',
      useraccountcontrol: '512',
      memberof: 'CN=lunch-users,OU=Groups CN=lunch-admins,OU=Groups ' +
        'CN=campus-all,OU=Groups' },
    { dn: 'CN=Park Hana,OU=Students', cn: 'Park Hana', sn: 'Park',
      samaccountname: 'hana.park', mail: 'hana.park@campus.example',
      objectclass: 'top person organizationalPerson user',
      useraccountcontrol: '512',
      memberof: 'CN=lunch-users,OU=Groups CN=campus-all,OU=Groups' },
    { dn: 'CN=Oh Jisoo,OU=Staff', cn: 'Oh Jisoo', sn: 'Oh',
      samaccountname: 'jisoo.oh', mail: 'jisoo.oh@campus.example',
      objectclass: 'top person organizationalPerson user',
      useraccountcontrol: '514',
      memberof: 'CN=campus-all,OU=Groups' },
    { dn: 'CN=Choi Yuna,OU=Students', cn: 'Choi Yuna', sn: 'Choi',
      samaccountname: 'yuna.choi', mail: 'yuna.choi@campus.example',
      objectclass: 'top person organizationalPerson user',
      useraccountcontrol: '512',
      memberof: 'CN=campus-all,OU=Groups' },
    { dn: 'CN=svc-keycloak,OU=Service Accounts', cn: 'svc-keycloak',
      sn: 'svc-keycloak', samaccountname: 'svc-keycloak',
      objectclass: 'top person organizationalPerson user',
      useraccountcontrol: '66048' },
    { dn: 'CN=lunch-users,OU=Groups', cn: 'lunch-users',
      samaccountname: 'lunch-users', objectclass: 'top group' },
    { dn: 'CN=lunch-admins,OU=Groups', cn: 'lunch-admins',
      samaccountname: 'lunch-admins', objectclass: 'top group' },
    { dn: 'CN=campus-all,OU=Groups', cn: 'campus-all',
      samaccountname: 'campus-all', objectclass: 'top group' }
  ];

  // 아주 작은 필터 해석기. ldap/proto/proto.go 의 규칙과 같은 것만 한다.
  function parseFilter(s, at) {
    at = at || { i: 0 };
    if (s[at.i] !== '(') throw new Error('( 로 시작해야 합니다');
    at.i++;
    var node;
    var c = s[at.i];
    if (c === '&' || c === '|') {
      at.i++;
      var subs = [];
      while (s[at.i] === '(') subs.push(parseFilter(s, at));
      if (!subs.length) throw new Error('&/| 안이 비었습니다');
      node = { op: c, subs: subs };
    } else if (c === '!') {
      at.i++;
      node = { op: '!', subs: [parseFilter(s, at)] };
    } else {
      var start = at.i;
      while (at.i < s.length && '=<>~)'.indexOf(s[at.i]) < 0) at.i++;
      var attr = s.slice(start, at.i);
      if (!attr) throw new Error('속성 이름이 없습니다');
      var op = '=';
      if ('><~'.indexOf(s[at.i]) >= 0) { op = s.slice(at.i, at.i + 2); at.i += 2; }
      else if (s[at.i] === '=') at.i++;
      else throw new Error('연산자가 없습니다');
      var vs = at.i;
      while (at.i < s.length && s[at.i] !== ')') at.i++;
      node = { op: op, attr: attr.toLowerCase(), val: s.slice(vs, at.i) };
    }
    if (s[at.i] !== ')') throw new Error(') 가 없습니다');
    at.i++;
    return node;
  }

  function matches(e, f) {
    if (f.op === '&') return f.subs.every(function (x) { return matches(e, x); });
    if (f.op === '|') return f.subs.some(function (x) { return matches(e, x); });
    if (f.op === '!') return !matches(e, f.subs[0]);
    var raw = e[f.attr];
    if (raw === undefined) return false;
    var vals = String(raw).toLowerCase().split(' ');
    var want = f.val.toLowerCase();
    if (f.op === '=' && want === '*') return true;
    if (f.op === '=' && want.indexOf('*') >= 0) {
      var re = new RegExp('^' + want.split('*').map(function (p) {
        return p.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      }).join('.*') + '$');
      return vals.some(function (v) { return re.test(v); });
    }
    if (f.op === '>=') return vals.some(function (v) { return v >= want; });
    if (f.op === '<=') return vals.some(function (v) { return v <= want; });
    // memberOf 처럼 값이 여럿인 칸은 하나라도 맞으면 된다
    return vals.some(function (v) { return v === want; }) ||
      String(raw).toLowerCase() === want;
  }

  function showTree(f, depth) {
    var pad = new Array(depth + 1).join('  ');
    if (f.subs) {
      var head = { '&': '그리고', '|': '또는', '!': '아님' }[f.op];
      return pad + head + '\n' + f.subs.map(function (s) {
        return showTree(s, depth + 1);
      }).join('\n');
    }
    return pad + f.attr + ' ' + f.op + ' ' + (f.val || '*');
  }

  __demo('ldap-filter', function (host, api) {
    var el = q(host, '[data-filter]');
    function run() {
      var s = val(el, '(&(objectClass=user)(sAMAccountName=minji))');
      var f;
      try {
        var at = { i: 0 };
        f = parseFilter(s, at);
        if (at.i !== s.length) throw new Error('뒤에 남은 글자가 있습니다');
      } catch (e) {
        api.w(host, '필터를 못 읽습니다 — ' + api.esc(e.message), 'bad');
        return;
      }
      var hit = DIR.filter(function (e) { return matches(e, f); });
      var out = '<span class="dim">' + api.esc(showTree(f, 0)) +
        '</span>\n\n';
      if (!hit.length) {
        out += '맞는 항목이 없습니다.';
        api.w(host, out, 'dim');
        return;
      }
      out += hit.map(function (e) { return '  ' + api.esc(e.dn); }).join('\n');
      out += '\n\n<span class="dim">' + hit.length + '건 / 전체 ' +
        DIR.length + '건</span>';
      api.w(host, out, 'ok');
    }
    on(el, 'input', run);
    run();
  });

  /* ── 9. DN 뜯어보기 ─────────────────────────────────────────────
   * DN 은 아래에서 위로 적힌 주소다. 그 순서가 거꾸로라는 것을
   * 한 번 눈으로 보면 다시는 헷갈리지 않는다. */
  var RDN_MEANING = {
    cn: '이름 (Common Name) — 사람·그룹의 이름',
    ou: '서랍 (Organizational Unit) — 조직 단위',
    dc: '도메인 조각 (Domain Component)',
    o: '조직 (Organization)',
    uid: '아이디 (주로 OpenLDAP 쪽)'
  };
  __demo('ldap-dn', function (host, api) {
    var el = q(host, '[data-dn]');
    function run() {
      var s = val(el, 'CN=Kim Minji,OU=Students,DC=ad,DC=campus,DC=example');
      var parts = s.split(',').map(function (p) { return p.trim(); })
        .filter(function (p) { return p.length; });
      if (!parts.length) {
        api.w(host, 'DN 을 써 보세요.', 'dim');
        return;
      }
      var lines = [], bad = 0;
      for (var i = 0; i < parts.length; i++) {
        var k = parts[i].indexOf('=');
        if (k < 0) { bad++; lines.push('  ' + parts[i] + '   ← = 가 없다'); continue; }
        var type = parts[i].slice(0, k).trim().toLowerCase();
        var v = parts[i].slice(k + 1).trim();
        var why = RDN_MEANING[type] || '(이 덱에서 다루지 않는 종류)';
        lines.push('  ' + (i === 0 ? '가장 아래 ' : '        ↑ ') +
          type.toUpperCase() + '=' + v);
        lines.push('             ' + why);
      }
      var tail = '\n<span class="dim">조각 ' + parts.length +
        '개 · 맨 앞이 그 항목 자신, 뒤로 갈수록 위쪽 서랍이다.\n' +
        '도메인은 DC 조각을 이어 붙이면 나온다 — ' +
        parts.filter(function (p) { return /^dc=/i.test(p.trim()); })
          .map(function (p) { return p.split('=')[1]; }).join('.') +
        '</span>';
      api.w(host, api.esc(lines.join('\n')) + tail, bad ? 'bad' : 'ok');
    }
    on(el, 'input', run);
    run();
  });

  /* ── 7. YAML 들여쓰기 검사기 ────────────────────────────────────
   * 2부부터 매니페스트를 읽는다. 그 전에 탭 하나로 죽는 경험을 여기서. */
  __demo('yaml', function (host, api) {
    var el = q(host, '[data-yaml]');
    var SAMPLE = 'apiVersion: v1\nkind: Service\nmetadata:\n  name: lunch\n' +
      'spec:\n  ports:\n    - port: 80';
    function run() {
      var text = val(el, SAMPLE);
      var lines = text.split('\n');
      var problems = [];
      var seen = [];
      for (var i = 0; i < lines.length; i++) {
        var ln = lines[i];
        if (!ln.trim() || /^\s*#/.test(ln)) continue;
        if (/^\s*\t/.test(ln) || /^ *\t/.test(ln)) {
          problems.push((i + 1) + '행: 탭이 있다. YAML 은 탭을 금지한다');
          continue;
        }
        var ind = ln.length - ln.replace(/^ +/, '').length;
        if (ind % 2 !== 0) {
          problems.push((i + 1) + '행: 들여쓰기가 ' + ind +
            '칸 — 이 파일은 2칸 단위다');
        }
        seen.push(ind);
        if (/:\S/.test(ln) && !/:\/\//.test(ln)) {
          problems.push((i + 1) + '행: 콜론 뒤에 빈칸이 없다');
        }
      }
      if (problems.length) {
        api.w(host, api.esc(problems.join('\n')), 'bad');
      } else {
        api.w(host, '들여쓰기 문제 없음 · 줄 ' + seen.length + '개', 'ok');
      }
    }
    on(el, 'input', run);
    run();
  });
  /* ── 10. PKCE 계산기 ────────────────────────────────────────────
   * verifier 를 넣으면 challenge 를 만들어 준다.
   * 한 글자만 바꿔도 전부 달라진다는 것을 손으로 확인하는 자리다. */
  __demo('pkce', function (host, api) {
    var el = q(host, '[data-verifier]');
    function run() {
      var v = val(el, 'lunch-demo-verifier-0123456789-abcdefghijklmnop');
      // RFC 7636 §4.1 — verifier 는 43~128글자여야 한다.
      var lenNote = v.length < 43
        ? '\n\n<span class="bad">짧다 — 규격은 43글자 이상을 요구한다 ' +
          '(RFC 7636 §4.1). 지금 ' + v.length + '글자.</span>'
        : '\n\n<span class="dim">verifier ' + v.length + '글자 · ' +
          '규격은 43~128글자 (RFC 7636 §4.1)</span>';
      var subtle = (window.crypto && window.crypto.subtle) || null;
      if (!subtle) {
        api.w(host, '이 브라우저에서는 계산할 수 없습니다 ' +
          '(https 로 열어야 Web Crypto 가 켜집니다).', 'dim');
        return;
      }
      subtle.digest('SHA-256', new TextEncoder().encode(v))
        .then(function (buf) {
          var b = new Uint8Array(buf), bin = '';
          for (var i = 0; i < b.length; i++) {
            bin += String.fromCharCode(b[i]);
          }
          // base64url — 1부 8장에서 본 그 변환이다.
          var chal = btoa(bin).replace(/\+/g, '-').replace(/\//g, '_')
            .replace(/=+$/, '');
          api.w(host,
            'verifier  ' + api.esc(v) + '\n' +
            '  ↓ SHA-256 → base64url\n' +
            'challenge ' + api.esc(chal) + lenNote, 'ok');
        }).catch(function (e) {
          api.w(host, '계산 실패: ' + api.esc(e.message), 'bad');
        });
    }
    on(el, 'input', run);
    run();
  });

  /* ── 11. JWT 해독기 ─────────────────────────────────────────────
   * 열쇠 없이 토큰을 읽는다. 그게 이 데모의 전부이자 요점이다 —
   * 읽을 수 있다는 것과 믿어도 된다는 것은 다른 일이다. */
  __demo('jwt', function (host, api) {
    var el = q(host, '[data-jwt]');

    // base64url 되돌리기. 패딩이 없으므로 채워서 푼다.
    function unb64(s) {
      var t = s.replace(/-/g, '+').replace(/_/g, '/');
      while (t.length % 4) t += '=';
      var bin = atob(t), bytes = new Uint8Array(bin.length);
      for (var i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
      return new TextDecoder().decode(bytes);
    }

    function pretty(json) {
      try {
        return JSON.stringify(JSON.parse(json), null, 2);
      } catch (e) {
        return json;
      }
    }

    function run() {
      var raw = val(el, '').replace(/\s+/g, '');
      var parts = raw.split('.');
      if (parts.length !== 3) {
        api.w(host, '조각이 ' + parts.length + '개다 — ' +
          '토큰은 점으로 나뉜 세 조각이다.', 'bad');
        return;
      }
      var head, body;
      try {
        head = pretty(unb64(parts[0]));
        body = pretty(unb64(parts[1]));
      } catch (e) {
        api.w(host, 'base64url 을 되돌릴 수 없다 — 토큰이 깨졌다.', 'bad');
        return;
      }
      api.w(host,
        '<span class="dim">머리 (header)</span>\n' + api.esc(head) +
        '\n\n<span class="dim">내용 (payload)</span>\n' + api.esc(body) +
        '\n\n<span class="dim">서명 ' + parts[2].length +
        '글자 — 여기서는 확인하지 않았다.\n' +
        '열쇠가 없어도 위의 두 조각은 이렇게 읽힌다.</span>', 'ok');
    }
    on(el, 'input', run);
    run();
  });
})();
