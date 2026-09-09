### [2026-09-09 03:20] Keycloak×AD 덱 전수 리뷰 — 사실오류 2건·모순 1건·상호참조 5건·표기 8건·레이아웃 1건 정정
- **기획:** PLAN §8 14단계. 1005장을 기계 검사 + 눈으로 훑어 결함을 종류별로 세었다.
- **TC:** deck/check_xref.py(신규)로 "N부 M장" 화살표를 전수 대조 — 상호참조 5건이 전부 여기서 나왔다. make all 에 넣었다.
- **개발:** deck/check_xref.py(신규) · Makefile · deck/base/head.html · deck/glossary.txt · deck/claims.md · sections 03·06·07·08·10·12 외 3개 파일
- **검증:** 1005장 · 커버리지 8998/8998줄 100% · 조립 0건 · 역검증 통과 · 상호참조 0건 · deck-check 0건 · 글꼴 통과 · test 14패키지
- **비고:** AD 는 1000건을 넘겨도 sizeLimitExceeded(4)를 준다 — "조용히 버린다" 가 아니라 받는 쪽이 흘려보내는 것이다. miniidp 를 "400줄" 이라 부른 곳 6개와 "약 1,100줄" 이라는 표가 서로 어긋나 있었다(실제 1,050줄). 12부의 세션 A/B 는 0부와 반대였다.

### [2026-09-09 02:40] Keycloak×AD 덱 공개 — 1005장, index·README 카드 함께
- **기획:** PLAN §8 13단계. 12부까지 다 들어와 '준비 중' 표지가 0개라 Makefile 에서 SKEL=1 을 뗐다.
- **TC:** make all 을 --skeleton 없이 돌려 deck-check 가 그대로 통과하는지 확인. rsvg-convert 로 system_p4·p12 를 PNG 로 떠서 눈으로 봤다.
- **개발:** index.html(웹&브라우저 절에 카드) · README.md(웹&인증 절에 행) · keycloak_ad/Makefile · keycloak_ad/PLAN.md
- **검증:** 1005장 · 커버리지 8998/8998줄 100% · 조립 0건 · 역검증 통과 · deck-check 0건(SKEL 없이) · 글꼴 통과 · test 14패키지
- **비고:** Makefile 도 부록에 전문이 실려 주석 한 줄(76칸)이 폭 검사에 걸렸다 — 접어서 해결. librsvg 는 fill:var(--…) 를 안 풀어 그냥 렌더하면 상자가 새까맣다. 색을 넣어 떠야 확인된다.

### [2026-09-09 02:17] Keycloak×AD 덱 12부 — 마무리 42장 (용어집·치트시트·FAQ·출처)
- **기획:** PLAN §8 12단계. 5개 장(요약 그림·용어집 83·치트시트·자주 묻는 것 15·출처), 퀴즈 1. 앞의 열두 부를 가리키는 부라 새 주장이 거의 없다.
- **TC:** deck/gen_glossary.py 가 용어의 "처음 나온 자리" 를 전수 대조한다(없는 id 면 조립 실패). check_deck.js 에 덱 안 #링크 검사(164개)를 새로 넣었다.
- **개발:** deck/glossary.txt(신규) · deck/gen_glossary.py(신규) · deck/build_deck.py · deck/check_deck.js · deck/sections/12_wrap.html · deck/claims.md
- **검증:** 1005장 · 커버리지 8997/8997줄 100% · 조립 0건 · 역검증 통과 · deck-check 0건(퀴즈 53·데모 12·내부링크 164) · 글꼴 통과 · test 14패키지
- **비고(§8.12 이탈 둘):** ① 용어집을 슬라이드의 data-term 대신 한 파일(glossary.txt)에서 만든다 — 뜻 83개가 열두 파일에 흩어지면 고르는 기준이 안 보인다. ② 치트시트에서 kcadm 을 뺐다. 이 덱은 관리 REST API 를 curl 로 직접 불렀고, 안 돌려 본 명령을 싣지 않는다.

### [2026-09-09 02:40] Keycloak×AD 덱 10·11부 — 운영 32장, 전체 훑기 15장
- **기획:** PLAN §8 11단계. 10부는 수명·열쇠 회전·비밀·들여다보기·장애 10가지·백업, 11부는 40단계 체크리스트(한다/보여야 한다/안 되면 어디를). 11부는 새 지식 없는 색인이다.
- **TC:** keycloak/ops_lab.sh 로 이벤트·세션·지표·열쇠 회전을 실제로 돌려 캡처했다.
- **개발:** keycloak/ops_lab.sh(신규) · keycloak/run_dev.sh · tools/record.sh · deck/sections/10_ops.html·11_walkthrough.html(신규) 외 2개 파일
- **검증:** 964장 · 커버리지 100% · 조립 0건 · 역검증 통과 · deck-check 0건(퀴즈 55·데모 12) · 글꼴 통과 · test 14패키지
- **비고:** /metrics 가 404 였다 — --metrics-enabled 를 따로 켜야 한다. 지표 이름을 짐작해 grep 했다가 빈 화면을 얻어, 있는 이름을 세어 고르도록 바꿨다. 둘 다 캡처의 경고로 남겼다.

### [2026-09-09 01:50] Keycloak×AD 덱 9부 — 권한 36장
- **기획:** PLAN §8 10단계. 6개 장(다섯 걸음·전후 토큰·그룹과 역할·client scope·최소 권한·관리자 화면), 퀴즈 2. 8부에서 앱이 본 groups 클레임이 어디서 왔는지 끝까지 되짚는다.
- **TC:** keycloak/authz_lab.sh 로 같은 사람의 전·후 토큰과 역할 매핑 결과를 캡처했다.
- **개발:** keycloak/authz_lab.sh(신규) · tools/record.sh · deck/sections/09_authz.html(신규) · 13_appendix.html · deck/claims.md
- **검증:** 914장 · 커버리지 8801/8801줄 100% · 조립 0건 · 역검증 통과 · deck-check 0건(퀴즈 54·데모 12) · 글꼴 통과 · test 14패키지
- **비고:** "역할은 매퍼 없이도 실린다" 고 썼다가 캡처에서 ID 토큰에 없는 것을 보고 고쳤다. 기본 roles scope 는 액세스 토큰에만 싣는다 — 그 함정을 본문의 경고로 만들었다.

### [2026-09-09 01:10] Keycloak×AD 덱 8부 — 서비스에 로그인 붙이기 41장
- **기획:** PLAN §8 9단계. 7개 장(세 갈래 길·oauth2-proxy·헤더 신뢰 경계·앱이 직접·약속 갚기·로그아웃 3종·다른 스택), 퀴즈 4. 0부의 그림이 이 부에서 전부 켜진다.
- **TC:** keycloak/app_e2e.sh 가 4부의 실행 파일을 다시 빌드하지 않고 -issuer 만 바꿔 진짜 Keycloak 에 붙인다. 로그인·이름·그룹·403/200 이 전부 캡처로 남았다.
- **개발:** keycloak/app_e2e.sh(신규) · k8s/base/oauth2-proxy.yaml(신규) · lunch-ingress-authreq.yaml(신규) · deck/sections/08_app.html(신규) 외 4개 파일
- **검증:** 878장 · 커버리지 8612/8612줄 100% · 조립 0건 · 역검증 통과 · deck-check 0건(퀴즈 52·데모 12) · 글꼴 통과 · validate.sh 세 벌 각 20개 통과 · test 14패키지
- **비고:** 헤더를 믿는 구조는 담장(NetworkPolicy)이 없으면 아무것도 안 지킨다는 것을 3장에서 크게 다뤘다. 그 한계가 길 2를 고르는 이유가 된다.

### [2026-09-09 00:10] Keycloak×AD 덱 7부 후반 — 설정 표·매퍼·동기화·진단 26장
- **기획:** PLAN §8 8단계. 4개 장(설정 칸 전수 표·매퍼 여섯 종·동기화 전체와 변경분·진단 15가지), 퀴즈 3. 7부가 75장으로 완료됐다.
- **TC:** ad_lab.sh 에 실험 둘을 더해(매퍼 목록·동기화 두 종) 캡처로 검증했다.
- **개발:** keycloak/ad_lab.sh · deck/sections/07_ad_federation.html · deck/claims.md
- **검증:** 829장 · 커버리지 8344/8344줄 100% · 조립 0건 · 역검증 통과 · deck-check 0건(퀴즈 48·데모 12) · 글꼴 통과 · test 14패키지
- **비고:** 변경분 동기화가 whenChanged 로 시각을 잘라 묻는 것을 캡처로 확인했고, 그 필터에 삭제를 볼 수단이 없다는 것이 "퇴사자가 남는" 이유임을 보였다.

### [2026-09-08 23:30] Keycloak×AD 덱 6부 — 쿠버네티스에 Keycloak 47장
- **기획:** PLAN §8 7단계. 6개 장(PostgreSQL StatefulSet·Keycloak 얹기·인그레스·여러 벌과 캐시·인증서와 NetworkPolicy·오퍼레이터/Helm), 퀴즈 4. 2부에서 배운 것을 그대로 쓰고 새 개념은 StatefulSet 하나다.
- **TC:** 매니페스트는 tier B — kubeconform -strict 가 관문이다. base·dev·prod 각 16개 오브젝트 통과.
- **개발:** k8s/base 4개 신규 · kustomization · overlays 둘 · certs/make_certs.sh · tools/pickobj.py(신규) · deck/sections/06_k8s_keycloak.html(신규) 외 3개 파일
- **검증:** 802장 · 커버리지 8297/8297줄 100% · 조립 0건 · 역검증 통과 · deck-check 0건(퀴즈 45·데모 12) · 글꼴 통과 · test 14패키지
- **비고:** YAML 접기(>-)로 나눈 DNS 이름에 공백이 끼어 깨지는 것을 직접 넣어 보고 확인했다. kustomize 가 루트 밖 파일을 못 읽어 make certs 가 CA 를 k8s/base 로 복사하게 했다.

### [2026-09-08 18:10] Keycloak×AD 덱 7부 전반 — AD 연동 49장
- **기획:** PLAN §8 6단계의 마지막. 7개 장(정할 것·로그인 한 번의 LDAP 질의·로그인 아이디·서비스 계정과 범위·LDAPS·그룹이 건너오는 길·계정 상태), 퀴즈 4. 후반(전수 표·진단 15·동기화·매퍼 6종)은 8단계로 남긴다.
- **TC:** 새 Go 코드는 없다. keycloak/ad_lab.sh 로 설정을 바꿔 가며 가짜 AD 로그가 어떻게 달라지는지를 캡처로 남기는 것이 이 부의 검증이다.
- **개발:** keycloak/ad_lab.sh(신규) · deck/sections/07_ad_federation.html(신규) · 13_appendix.html · deck/claims.md(18행) · tools/record.sh
- **검증:** 742장 · 커버리지 7829/7829줄 100% · 조립 0건 · 역검증 통과 · deck-check 0건(퀴즈 41·데모 12) · 글꼴 통과 · test 14패키지
- **비고:** 실험들이 서로 상태를 남겨 답이 어긋난 것을 고쳤다(사본 삭제·설정 되돌리기). 관리 API 의 PUT 이 합치기라 키를 빼는 것만으로는 설정이 안 지워진다. 7부 id 가 3부와 겹쳐 f7- 로 바꿨다.

### [2026-09-08 17:20] Keycloak×AD 덱 5부 본문 — Keycloak 이란 74장
- **기획:** PLAN §8 6단계의 가운데. 11개 장(제품과의 차이·dev/prod·설정 세 경로·realm·client·user/group/role·scope와 mapper·federation·관리 API·내보내기·마무리), 퀴즈 7. 4부의 miniidp 와 나란히 두는 장을 여럿 뒀다.
- **TC:** 본문 커밋이라 새 시험은 없다. 조립기 검사와 역검증·deck-check·글꼴검사가 관문이다.
- **개발:** deck/sections/05_keycloak.html(신규) · 13_appendix.html(FULLSRC 12개) · deck/claims.md(5부 24행) · deck/pending.txt(비움)
- **검증:** 687장 · 커버리지 7588/7588줄 100% · 조립 0건 · 역검증 통과 · deck-check 0건(퀴즈 37·데모 12) · 글꼴 통과 · test 14패키지
- **비고:** 안내문 칸 수(11 대 56)·토큰 클레임 표로 "제품이란 무엇인가" 를 숫자로 보였다. 8장의 가짜 AD 로그가 7부 예고편 노릇을 한다.

### [2026-09-08 16:40] Keycloak×AD 덱 6단계(1/3) — 진짜 Keycloak 26.7.3 연동
- **기획:** PLAN §8 6단계의 앞부분. 배포판을 받아 띄우고, 관리 REST API 로 realm·클라이언트·AD 연동을 세우고, 로그인 전 과정을 curl 로 훑어 캡처한다. 본문은 다음 두 커밋.
- **TC:** 새 Go 코드 2건 RED→GREEN — 이진 필터를 RFC 4515 `\XX` 로 감싸기(proto), 긴 필터를 `)(` 에서 접기(fakead). 나머지는 실물 실행이 관문이다.
- **개발:** keycloak/ 스크립트 7개 · keycloak/json 6개 · realm-campus.json(내보낸 것) · tools/record.sh 9절 · ldap/proto/proto.go · ldap/fakead/server.go 외 2개 파일
- **검증:** 진짜 Keycloak 이 가짜 AD 에서 사용자 7명·그룹 3개를 가져오고, 4부의 jwtool 이 그 토큰을 그대로 검증했다. 빈 DB 에 realm 재수립 후 로그인 통과. test 14패키지 · 캡처 121개 3회 md5 동일
- **비고:** kc_* 캡처 12개는 재현 불가 — Keycloak 이 realm 마다 서명 열쇠를 새로 만든다. 그 사실을 캡처로 남겼다. require_free 가 HTTP 로만 두드려 LDAP 유령을 못 잡던 것을 TCP 검사로 고쳤다.

### [2026-09-08 17:10] Keycloak×AD 덱 2부 본문 — 쿠버네티스 71장
- **기획:** PLAN §8 4단계. 9개 장(컨테이너·Pod·Deployment·Service·Ingress·설정과 비밀·Kustomize·검사·마무리), 퀴즈 6, 데모 2. 클러스터가 없으므로 "띄우는" 대신 "읽고 검증하는" 것으로 배운다.
- **TC:** miniapp 의 pickSecret 만 새 코드라 RED→GREEN 3건(환경 변수 우선·깃발 대체·둘 다 없으면 거절). 매니페스트는 kubeconform -strict 가 관문이다.
- **개발:** k8s/base 4개 · k8s/overlays 2개 · k8s/examples/typo.yaml · k8s/validate.sh · tools/fetch_k8s_tools.sh · tools/kexplain.py · deck/sections/02_k8s.html 외 5개 파일
- **검증:** 587장 · 커버리지 6853/6853줄 100% · 조립 0건 · 역검증 통과 · deck-check 0건(퀴즈 30·데모 12) · 글꼴 통과 · make record 3회 md5 동일 · test 14패키지 · validate.sh 3벌 통과
- **비고:** kubectl explain 과 --dry-run=client 가 서버를 부른다는 것을 확인해 그 사실을 캡처로 남기고, 필드 설명은 공개 JSON 스키마를 읽는 kexplain.py 로 대신했다. YAML 함정 캡처를 손으로 적었다가 진짜 파서에 넣어 보니 절반이 틀려 사실에 맞췄다.

### [2026-09-08 15:40] Keycloak×AD 덱 4부 본문 — 116장, 커버리지 100%
- **기획:** PLAN §8 5단계의 마지막. 9개 장(위임의 이유·인가 코드 흐름·state/nonce/PKCE·토큰 세 장·JWT 해부·JWKS와 안내문·앱 쪽·세 세션과 로그아웃·직접 돌려 보기), 퀴즈 8, 데모 2.
- **TC:** 본문 커밋이라 새 시험은 없다. 조립기의 검사(폭·장수·근거 배지·커버리지)와 역검증·deck-check·글꼴검사가 관문이다.
- **개발:** deck/sections/04_sso.html(신규), 13_appendix.html(FULLSRC 11개), deck/demos.js(+2), deck/claims.md(4부 28행), deck/pending.txt(비움), tools/showurl.py(신규), tools/record.sh, tools/scrub.py 외 1개 파일
- **검증:** 504장 · 커버리지 6465/6465줄 100% · 조립 0건 · 역검증 통과(코드 274·출력 99) · deck-check 0건(퀴즈 24·데모 11) · 글꼴 통과 · make record 3회 md5 동일(94개) · test 14패키지
- **비고:** 200칸 넘는 주소를 실을 수 없어 tools/showurl.py 로 칸마다 한 줄씩 펼쳤다. alg=none 사고의 연도를 적었다가 근거를 못 대 빼고 RFC 8725 로 대신했다. 0부와 4부의 세 세션 표가 어긋나 0부에 맞췄다.

### [2026-09-08 13:55] OIDC 전 과정 실물 — miniapp·jwtool, 캡처 32개
- **기획:** PLAN.md §8 5단계의 가운데. 앱(RP) 쪽과 토큰을 눈으로 보는 도구. miniapp 시험이 진짜 IdP를 상대하도록 miniidp를 라이브러리+cmd로 갈랐다(fakead와 같은 방식).
- **TC:** 뼈대→RED→GREEN. miniapp은 진짜 miniidp를 띄워 브라우저처럼 따라가는 통합 시험(로그인·403·state 재사용·nonce 바꿔치기·남의 열쇠·로그아웃). jwtool은 alg=none·변조·기한·대상·발급자. 새 시험 4종은 변이를 넣어 실제로 무는지 확인했다.
- **개발:** oidc/miniapp, oidc/jwtool, oidc/miniidp(분리), tools/tamper_jwt.py, tools/record.sh 7절, tools/scrub.py, ldap/fakead/server.go, deck/sections/01_web.html 외 3개 파일
- **검증:** test 14패키지 · vet·gofmt·72칸 폭 통과 · make record 3회 md5 동일(88개) · 조립 오류 0건 · 역검증 307장 통과 · deck-check 0건 · 글꼴 통과
- **비고:** 캡처하다 결함 4건을 찾아 고쳤다 — 로그아웃이 콜백으로 돌아가 400(PostLogoutURIs 분리), 가짜 AD의 SEARCH 로그 143칸(접어 적기), go test 캐시로 캡처가 두 판(-count=1), 토큰의 iat·jti로 재현 불가(FixForCapture). 4부 본문은 다음 커밋.

### [2026-09-08 11:25] OIDC 기초 — JWT·PKCE, LDAP 클라이언트 분리
- **기획:** PLAN.md §8 5단계의 앞부분. 토큰을 만들고 확인하는 층(jwt)과 가로챈 코드를 못 쓰게 만드는 층(pkce). miniidp 가 AD 에 물어보려면 LDAP 클라이언트가 라이브러리여야 해서 ldapcli 에서 뽑아냈다.
- **TC:** 셋 다 뼈대→RED→GREEN. jwt 는 RFC 7515 A.1·RFC 7519 §3.1 골든 벡터와 공격 넷(alg=none·alg 혼동·내용 변조·남의 열쇠), pkce 는 RFC 7636 부록 B 벡터. client 는 진짜 가짜 AD 를 띄워 놓고 시험한다.
- **개발:** oidc/jwt oidc/pkce, ldap/client(신규), ldap/fakead 를 라이브러리+cmd 로 분리, ldapcli 를 client 위로, tools/record.sh(본문 전용 캡처)
- **검증:** test 12패키지 · vet 통과 · make record 3회 md5 동일(54개) · 조립 오류 0건 · 역검증 통과 · deck-check 0건 · 글꼴 통과 · width 18파일 통과
- **비고:** TLS 1.3 세션 티켓이 악수 뒤에 비동기로 와서 -v 캡처의 줄 번호가 가끔 밀렸다. 본문만 따로 뜨는 캡처를 더해 인용을 그쪽으로 옮겼다. miniidp·miniapp·jwtool 과 4부 본문은 다음 커밋.

### [2026-09-08 10:42] 3부 본문 — 회사 계정의 세계 83장, 전체 소스 부록 100장
- **기획:** PLAN.md §8 3단계 뒷부분. 디렉터리·DN·AD 속성·그룹/memberOf·BER 바이트·바인드·검색·LDAPS·서비스 계정·안 하는 것·마무리 9개 장. 소스 전문은 새 부록 절이 싣는다.
- **TC:** 로그 폭 시험을 새로 써서 RED 확인 → Server.Close 가 유휴 연결 때문에 안 꺼지던 결함을 잡아 연결 추적을 넣었다. 진단 문구 접기(wrapCells)도 RED→GREEN.
- **개발:** deck/sections/{03_ad,13_appendix}.html, deck/figs/ad_tree.svg, deck/demos.js(ldap-filter·ldap-dn), ldap/fakead/server.go, ldap/ldapcli/dump.go, deck/{order,budget,pending}.txt, Makefile
- **검증:** 덱 309장 572 KB · 소스 커버리지 3833/3833줄 100퍼센트 · 조립 오류 0건 · 역검증 통과(코드 159·출력 62) · deck-check 0건 · 글꼴 통과 · make record 2회 md5 동일(52개) · test 8패키지 · vet 통과
- **비고:** 3부 83장(목표 75). 부록은 §7 에 없던 절이라 13번으로 새로 뒀다 — 커버리지 약속(§2.1)을 지키면서 교육 장을 안 부풀리는 자리. 예상 합계 989장(상한 2000).

### [2026-09-08 09:20] LDAP 코어 — BER·프로토콜·가짜 AD·ldapcli, 캡처 14개
- **기획:** PLAN.md §8 3단계 앞부분. Keycloak 이 AD 에게 실제로 묻는 것만 골라 흉내 내는 LDAP 서버와, 오간 바이트를 풀어 보여 주는 클라이언트. 표준 라이브러리만 씀.
- **TC:** 네 묶음 모두 뼈대→RED→GREEN. BER 는 골든 바이트(익명 바인드 14바이트·정수/길이 표), 필터는 글↔나무↔바이트 3방향 왕복, 서버는 진짜 소켓으로 종단 시험(쪼개 보내기·LDAPS 악수·잠금).
- **개발:** ldap/ber ldap/proto ldap/fakead(dir·server·main) ldap/ldapcli(dump·main), data/campus.ldif(15항목), tools/record.sh 3부 캡처
- **검증:** go test 8패키지 통과 · vet 통과 · make record 2회 md5 동일(52개) · 조립 오류 0건 · 역검증 통과 · deck-check 0건 · 글꼴 통과
- **비고:** 덱 본문(3부)은 다음 커밋. 소스 2,300줄이 deck/pending.txt 에 대기 중. AD 진단 코드(52e·533·775·525)와 memberOf 계산·objectGUID 16바이트 이진값을 그대로 재현했다.

### [2026-09-08 08:40] Keycloak×AD 덱 1부 — 웹이 돌아가는 법 104장, 서버 4종·캡처 38개
- **기획:** PLAN.md §8 2단계. 웹을 처음 만지는 사람 기준으로 HTTP·상태코드·리다이렉트·폼·쿠키·TLS·도구상자를 한 장에 한 개념씩. 코드는 전부 실행되는 실물, 출력은 전부 진짜 캡처.
- **TC:** 02·03·04 는 뼈대만 두고 RED 확인 후 GREEN(총 40개 테스트). 01 은 구현이 먼저라 정렬·Host·404 를 일부러 깨뜨려 시험이 무는지 확인. TLS 는 진짜 악수 3종(우리 CA 신뢰/불신/이름 불일치).
- **개발:** web/01_hello · 02_form_cookie · 03_redirect · 04_tls (+테스트), tools/{record.sh,scrub.py,width.py,rewrap.py}, deck/{demos.js,budget.txt,pending.txt}, deck/sections/01_web.html 외 3개 파일
- **검증:** go test 4패키지 통과 · vet 통과 · make record 3회 md5 동일(38개) · 조립 오류 0건 · 역검증 통과(코드 33·출력 44 전부 일치) · deck-check 0건 · 글꼴 --check 통과. 덱 127장 315 KB.
- **비고:** scrub 이 sha256 출력까지 가짜로 바꾸던 것을 잡아 '자리로 고르는' 방식으로 고쳤다. go run 유령 프로세스가 옛 코드의 출력을 캡처하던 것도 잡아 빌드 후 실행+포트 선점 검사로 바꿨다. 1부가 목표 80장 대비 104장 — 예상 합계 882장(상한 1000)이라 아직 여유 있다.

### [2026-09-08 07:10] Keycloak×AD 덱 뼈대 — 빌더·표지 12장·부 표지 12장
- **기획:** PLAN.md §8 1단계. 덱 조립 도구 일습과 0부(표지·전체 그림·세 세션·근거 등급·등장인물)를 세우고, 1~12부는 표지만 두어 처음부터 열리는 상태를 만든다.
- **TC:** `deck/check_deck.js` 를 먼저 써서 RED(덱 없음) 확인 → 구조·상호참조·자기완결성 8종 검사. `certs/check_certs.sh` 도 RED(인증서 없음) → 체인·SAN·EKU·키 짝 검사.
- **개발:** keycloak_ad/{go.mod,Makefile,.gitignore}, deck/{build_deck,verify_deck,chunks,gen_system}.py, deck/check_deck.js, deck/base/{head,tail}.html, deck/sections/ 13개, deck/figs/ 13개, certs/{make,check}_certs.sh, deck/claims.md
- **검증:** make all SKEL=1 — 조립 오류 0건 · 역검증 통과 · deck-check 오류 0건 · 글꼴 --check 통과. 24장 171 KB. 인증서 검사 오류 0건.
- **비고:** PLAN.md §5 는 boricha 도구 재사용을 지시했으나, boricha 계열은 `<section class="slide">` 구조라 template.html 의 `__demo`·`.quiz`·`#ch` 상호참조와 맞지 않는다. 저장소 다수(덱 20여 개)가 쓰는 template 계열 = rts/deck 조립기 계보로 바꿨다. index·README 카드는 PLAN §8 13단계(공개)에서 함께 넣는다.

### [2026-09-08 06:49] Keycloak×AD 연동 덱 — Opus 빌드 세션용 작업 계획 작성
- **기획:** k8s 서비스에 Keycloak으로 AD 로그인을 붙이는 과정을 웹 개념이 없는 대학 4학년 눈높이로 설명하는 덱(≈800장, 상한 1000)의 에이전트용 플랜. 12부 구성·증거 등급(실행/구문/문서)·fakead·miniidp 미니어처 설계·커밋 14단계.
- **TC:** 해당 없음(계획 문서). 이 기기 도구 현황(docker·kubectl 없음, Java21·Go1.27 있음, RAM 여유 2.2GB)을 확인해 §3에 고정.
- **개발:** keycloak_ad/PLAN.md
- **검증:** UTF-8 확인, §10 결정 7건 사용자 기본값 확정 반영
- **비고:** 실제 덱·소스는 Opus 세션이 PLAN.md 순서대로 진행. Keycloak 실행은 메모리 게이트(≥1.8GB) 통과 시에만.

### [2026-09-07 05:51] 보리차 덱 14장 키 배치표 — 펼친 폴더블(~768px)에서 옆 칸을 덮어쓰던 것 정정
- **기획:** `.keys` 격자의 칸 최소폭 9rem 은 테트리스 덱의 "← →" 용이었다. 보리차엔 "go run ./examples/01_hello" 같은 긴 nowrap 명령이 들어와 4칸으로 쪼개지는 768px 부근에서 넘쳤다.
- **TC:** 폭별 칸 수 계산(374px 1칸·768px 2칸·1120px 3칸)과 가장 긴 명령+설명 폭 대조. `make deck` 오류 0건·`make deck-check`·글꼴 `--check` 통과.
- **개발:** boricha/deck/extra.css(최소폭 18rem, `.keyrow>b` 자식 선택자, span min-width:0), boricha/deck/sections/00_start.html(13장 로그를 끝 13줄로), 나만의_Bubble_Tea_만들기.html 재조립
- **검증:** make deck 오류 0건, make deck-check 오류 0건, embed_mono_font --check 통과
- **비고:** 13장 "make deck 의 끝부분"이 커밋본에선 0줄(빌드 중 로그가 비어 있던 시점에 읽힘)이었던 것을 함께 바로잡았다. 실기기 확인은 못 했으니 폴드8에서 재확인 필요.

### [2026-09-07 05:17] 보리차 덱 2차 리뷰 — 사실오류 26건·모순 6건·표기 4건·코드 절단 11파일 재정렬·테마를 보리차 배색으로
- **기획:** 502장을 두 몫으로 나눠 전수 재검토(서브에이전트 2개). 소스가 자란 뒤 슬라이드의 코드 절단 범위가 함수 경계에서 밀려 캡션과 다른 코드를 보이던 것을 발견해 11개 소스 파일을 다시 잘랐다. 테트리스 덱에서 물려받은 남색·청록 배색을 보리차(볶은 갈색·호박색·크림)로 교체.
- **TC:** 절단 범위가 1..N 을 빈틈·중복 없이 덮고 45줄 이하인지 스크립트로 검증, 벤치 숫자를 out/bench.txt 와 대조, 모듈 캐시(bubbletea·ultraviolet·lipgloss·bubbles·go-runewidth)로 남의 소프트웨어 주장 대조, 배색 대비율 계산(본문 15.5:1, 보조 8.9:1).
- **개발:** deck/base/{deck_head,deck_tail_scripts}.html, deck/extra.css, deck/sections/{01..14b}.html, deck/claims.md(#23~26 추가), tea/program.go·style/style.go·width/width.go·examples/05_window 주석, index.html·README.md(503장) 외 3개 파일
- **검증:** make deck 503장 오류 0건 커버리지 12350/12350, deck-check 전 항목 통과, embed_mono_font --check 통과, go vet 통과, go test 8패키지 ok
- **비고:** Bubble Tea v2 사건 큐는 무제한이 아니라 버퍼 없는 채널, Key.String() 은 공백도 "space"(우리와 같음), ▁▂▃ 블록은 N 이 아니라 A(모호), Style 은 100이 아니라 300바이트, 렌더 벤치 76→86us — 전부 실물 대조로 정정. 부록에 "주장과 근거 ③" 한 장이 늘어 503장.

---
## Archive
- [2026-09](history/archive/history-2026-09.md) — 15 entries
