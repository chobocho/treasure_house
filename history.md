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

### [2026-09-07 04:22] 보리차 덱 리뷰 — 사실오류 5건·표기 4건·상호참조 5건·중복 제목 10건 정정
- **기획:** 완성된 502장을 처음부터 훑어 숫자·사실·상호참조를 소스와 대조. 손으로 쓴 예시 코드가 생기면서 표지의 약속이 더는 참이 아니게 된 것을 바로잡음.
- **TC:** 덱이 언급한 시험 이름 전수 존재 확인, make 타깃 전수 확인, U+FFFD 검사, 중복 슬라이드 제목 검사, go list -deps 로 2부 의존 표 대조. 예시 시험 둘을 실제 파일로 만들어 시험 3종 추가.
- **개발:** deck/sections/{00,01,02,03,06,12,13}.html, deck/claims.md, tea/example_test.go, style/join.go·apps/{bugs,monitor}·examples/{01_hello,03_keys} 주석, index.html·README.md 숫자
- **검증:** make deck 502장 오류 0건 커버리지 12350/12350, deck-check 전 항목 통과, embed_mono_font --check 통과, go test 전 패키지 통과
- **비고:** 기능키 번호(14는 F4·16이 빈 자리), 간접 의존 15개, D2Coding 저작권 NHN, 시험 비율 3분의 1 — 전부 실물 대조로 정정.

### [2026-09-07 04:12] 보리차 덱 완성 — 8~14부 집필과 카드 등록 (501장)
- **기획:** 8부 style(34장)·9부 widgets(44장)·10부 testkit(27장)·11부 응용(26장)·12부 대조(16장)·13부 마무리(21장)·부록. 12부에 실을 실제 성능 수치를 위해 벤치마크 네 벌을 추가하고 make bench 로 out/bench.txt 를 남김.
- **TC:** 벤치 20종(폭·렌더·파서·스타일), 전 패키지 시험 유지. 조립마다 커버리지 12280/12280·오류 0건, check_deck.js 전 항목 통과, embed_mono_font.py --check 통과.
- **개발:** deck/sections/{08..13,14b}.html, {width,render,input,style}/bench_test.go, Makefile bench, out/{bench,binsize}.txt, index.html 카드, README.md 행
- **검증:** make deck 501장 오류 0건 · 1344KB, 기록 7종·터미널 캡처 19개 재생 정상
- **비고:** 한 프레임(한 줄 변경) 76us — 60fps 예산 16,666us 의 0.5퍼센트. 스타일 값 복사 130ns·할당 0. 숫자로 말할 수 있게 됨.

### [2026-09-07 03:47] 보리차 덱 본문 — 4~7부 집필 (350장)
- **기획:** 4부 term(28장·플랫폼 갈래와 정리 순서), 5부 input(44장·모든 바이트 경계 계약), 6부 render(24장·바이트 골든), 7부 width(23장·모호 폭 결정과 글꼴 이야기).
- **TC:** 조립마다 커버리지 전 줄·오류 0건. 6부는 tmux wrap before/after 캡처, 7부는 width_bad/ok 재생 기록을 슬라이드에 실어 함정을 눈으로 보이게 함.
- **개발:** deck/sections/{04_term,05_input,06_render,07_width}.html
- **검증:** make deck 350장 오류 0건, make deck-check 전 항목 통과
- **비고:** 덱이 싣는 D2Coding 이 ①②③ 을 두 칸으로 그리는 것을 7부에서 그대로 다룸 — 빌더 경고가 슬라이드의 근거가 된다.

### [2026-09-07 03:37] 보리차 덱 본문 — 0~3부 집필 (265장)
- **기획:** 0부(완성품·약속), 1부(터미널의 실체 27장), 2부(설계 15장), 3부(tea 핵심 루프 46장). 코드는 전부 실제 파일에서 잘라 오고, 화면은 tmux 캡처를 그대로 싣는다.
- **TC:** 조립할 때마다 커버리지 전 줄·오류 0건 확인. 인라인 SVG 도해 4종을 rsvg-convert 로 PNG 렌더해 눈으로 확인(Elm 순환도 라벨 겹침 1건 수정).
- **개발:** deck/sections/{00_start,01_terminal,02_design,03_tea}.html, deck/claims.md(주장 20건과 출처)
- **검증:** make deck 265장 오류 0건, make deck-check 전 항목 통과
- **비고:** VT100 1978·ANSI X3.64 1981·DEC 모드들·UAX #11·Bubble Tea v0.7.0(2020-05-26) 등 사실 주장은 전부 웹으로 확인해 claims.md 에 출처를 남김.

### [2026-09-07 03:18] 보리차 10단계 — 덱 빌드 체계 이식과 뼈대
- **기획:** tetris_tui/deck 도구 일습을 boricha/deck 으로 복사하고 제목·브랜드·출력 경로·기록 목록·커버리지 대상만 교체. 15개 부의 sections.json 과 스텁을 만들어 파이프라인 전체를 먼저 통과시킴.
- **TC:** 첫 조립에서 커버리지 12078/12078·오류 0건, check_deck.js 전 항목 통과(기록 7종 마운트·재생, DeckMono woff2 내장, 고정폭 목록 7곳 전부 우선).
- **개발:** deck/{build_deck,gen_appendix,gen_fonts,hl,chunks,split_ranges,test_fonts,untab}.py, player.js, check_deck.js, extra.css, base/, sections/ 스텁 15개
- **검증:** make deck → 181장 1006KB, make deck-check 오류 0건
- **비고:** 글꼴 폭 계약을 모호(A) 글자에 한해 경고로 완화. D2Coding 이 ①②③ 을 두 칸으로 그리는 것은 글꼴 잘못이 아니라 그 글자의 성질이다 — 칸이 맞아야 하는 캡처에는 쓰지 않는다.

### [2026-09-07 03:11] 보리차 9단계 — 캡스톤 셋: 할 일·시스템 모니터·전시장
- **기획:** 지금까지 쌓은 층을 전부 쓰는 응용 셋. 파일 입출력·주기적 표본 수집·화면 나누기를 각각 맡는다. 모델은 apps/ 라이브러리에 두고 cmd/ 는 얇게 — tools/record 가 import 해야 하기 때문(package main 은 import 불가).
- **TC:** todo 12종(추가·빈 값 거부·취소·완료·삭제·같은 글 중복·거른 상태 삭제·거르는 중 타이핑·저장/불러오기·없는 파일·배치 비활성·화면 크기), monitor 6종(CPU 차분 6경우·메모리·실제 /proc·스파크라인 6종과 폭 불변·멈춤/재개·화면 크기), showcase 5종(탭 순환·키 기록·모든 탭 크기·눈금 정렬과 길이·마우스).
- **개발:** apps/{todo,monitor,showcase}, cmd/{todo,monitor,showcase}, tools/record 등록부, Makefile 앱 캡처 규칙
- **검증:** go test 전 패키지 통과, make record 두 번 md5 동일, tmux 76×22 실캡처 3종, 누적 12,074줄
- **비고:** 거른 목록에서 값으로 지우면 글이 같은 항목 중 앞의 것이 지워진다 — 자리 번호를 항목에 붙여 해결.

### [2026-09-07 02:59] 보리차 8단계 — testkit·record·ansi2html과 함정 시연
- **기획:** 덱의 모든 화면을 실제 실행에서 뽑기 위한 장치. 진짜 Program 은 고루틴과 시계 위에 있어 결정론이 안 되므로, 같은 규칙을 시계 없이 다시 쓴 testkit 을 만들고 진짜 Program 과 대조하는 시험으로 지켜본다. 각본은 진짜 터미널 바이트로 바뀌어 진짜 파서를 지난다.
- **TC:** 각본 문법 10종·오류 5종·걸음→바이트 16종, 프레임 모양 불변, 프레임 수·이름표 짝, **두 번 돌려 프레임 동일(결정론)**, 기다리기가 명령을 돌림, q 조기 종료, 색 수준 지정, **진짜 Program 과 최종 모델 일치**, tea.Expand.
- **개발:** testkit/{script,testkit}.go, tools/{record,ansi2html}, apps/bugs, cmd/bugs, tea/cmd.go(Expand), Makefile record/html/logs
- **검증:** go test 전 패키지 통과, make record 두 번 md5 동일, tmux before/after 캡처 2종, 누적 10,556줄
- **비고:** 줄 넘침 함정은 우리 tea 로는 재현 불가 — 렌더러가 이미 자른다. 그래서 프레임워크를 거치지 않는 판으로 시연한다.

### [2026-09-07 02:45] 보리차 7단계 — widgets 부품 일곱 종
- **기획:** Bubbles 부분집합. 부품도 앱과 같은 모양(값 모델·Update·View)이되 Update 가 자기 타입을 돌려줘 부모가 그대로 대입한다. 키 배치와 도움말 문구를 한 값(Binding)에 묶어 둘이 어긋날 자리를 없앰.
- **TC:** Binding 일치·비활성·값 독립, 도움말 짧은/펼친 형태와 폭 제한, 스피너 회전·되감기·중복 울림 차단·그림 폭 일치, 진행 막대 경계(NaN·음수·초과·좁은 폭), 입력창 한글 룬 단위·커서·ctrl+u/w·글자수 제한·붙여넣기·초점·가로 스크롤·폭 불변, 목록 커서/스크롤/거르기(대소문자·커서 되돌림·거르는 중 j 입력), 뷰포트 모양 불변·클램프·휠·키 배치 일치.
- **개발:** widgets/{keymap,help,spinner,progress,textinput,list,viewport}.go, examples/10_widgets
- **검증:** go test 전 패키지 통과, go vet 무경고, 교차 컴파일 유지, tmux 실캡처(부품 6종 한 화면·한글 열 정렬·거르기 3/6), 누적 8,733줄
- **비고:** 거르는 중에는 모든 키가 입력창으로 가야 한다 — 안 그러면 "java" 를 칠 수 없다.

### [2026-09-07 02:32] 보리차 6단계 — tea 핵심 루프와 예제 사다리 01~09
- **기획:** Elm 아키텍처. 모델은 값, Update 는 고친 복사본과 Cmd 를 돌려준다. 고루틴 셋(입력·명령·주 루프)과 채널 하나. 루프 자체는 30줄이고 나머지 코드는 그 30줄을 짧게 유지하려고 있다.
- **TC:** 루프 갱신·EOF 종료·시작 사건(크기·색 수준), Init Cmd, Batch 동시성(느린 것 먼저 넣어도 빠른 것 먼저 도착), Sequence 순서, nil Cmd 무시, Tick/Every 1회성과 재예약 패턴, 밖에서 Send, 렌더러 유무, 종료 정리, 패닉 뒤 터미널 복구, 복사본 안 돌려주면 변경 사라짐.
- **개발:** tea/{msg,key,model,cmd,options,program}.go, examples/01~09, Makefile tmux-smoke 재작성
- **검증:** go test 전 패키지 통과, go vet 무경고, 교차 컴파일 유지, tmux 80×24 실캡처 10종(마우스 SGR·붙여넣기 한 덩어리·키 이름 확인), 누적 6,716줄
- **비고:** 마우스·붙여넣기는 tmux send-keys -H 로 실제 바이트를 밀어 넣어 증명함.

### [2026-09-07 02:19] 보리차 5단계 — render 줄 단위 diff 렌더러
- **기획:** 매 프레임 전체를 다시 그리면 깜빡인다. View 문자열을 화면 크기로 자른 Frame 으로 만들고, 지난 프레임과 줄 단위로 비교해 달라진 줄만 고쳐 쓴다. Write/Flush 를 나눠 초당 fps 번으로 제한.
- **TC:** Frame 자르기 7종(폭·높이·한글·꾸밈), Diff 7종(늘고 줄고 사라짐), 렌더러 바이트 골든 9종(첫 그리기·무변화 무출력·줄 축소 잔상 지우기·Repaint·Resize·Clear·동기화출력·오버플로), 줄 끝 공백 제거 7종과 diff 오염 방지, 시계 Start/Stop.
- **개발:** render/{buffer,diff,renderer,cursor}.go + 테스트 4개
- **검증:** go test 전 패키지 통과, go vet 무경고, 교차 컴파일 유지, 누적 4,977줄
- **비고:** 줄 끝 공백은 \e[K 덕에 뗄 수 있지만 배경색이 걸린 줄은 예외 — 그 공백이 색칠된 칸이다.

### [2026-09-07 02:13] 보리차 4단계 — style 꾸미기 층(Lip Gloss 부분집합)
- **기획:** 값 의미론 스타일. 색 프로필(없음/16/256/24비트) 판별과 내림 맞춤, 패딩·여백·정렬·테두리를 8단계 파이프라인으로 고정. 폭 계산은 전부 width 패키지 경유.
- **TC:** SGR 합성 9종, 값 복사 독립성, 패딩 CSS 4규칙, 폭·정렬·높이, 테두리 5종과 변 고르기, 파이프라인 순서(배경은 패딩까지만), 테두리 색, "모든 줄 폭 동일" 불변식, Join/Place 15종, 색 시퀀스 20종·프로필 판별 12종.
- **개발:** style/{color,palette,border,style,render,join}.go + 테스트 3개
- **검증:** go test 전 패키지 통과, go vet 무경고, 교차 컴파일 유지, 누적 4,319줄
- **비고:** 24비트→16색 내림에서 RGB 거리는 분홍을 은색으로 고른다. redmean 가중식으로 교체(49645 대 48900) — 덱의 비교 슬라이드 재료.

### [2026-09-07 02:05] 보리차 3단계 — width 글자 폭 표(한글 두 칸 문제)
- **기획:** 터미널은 글자를 칸으로 센다. 한글·한자·이모지는 두 칸. Go 표준 라이브러리에 답이 없어 유니코드 East_Asian_Width 표를 직접 실어 이분 탐색한다. 네트워크가 없어 자료는 python unicodedata(16.0.0)에서 뽑아 형식과 출처를 파일 머리에 명시.
- **TC:** RuneWidth 23종(한글·전각·이모지·결합문자·한글자모·제어), StringWidth ANSI 무시, Truncate 경계(반 칸 불가·꾸밈 보존·0/음수), Pad, Wrap 낱말·강제분할·줄바꿈 보존, 폭 2~20 전수로 "어느 줄도 폭 초과 없음" 불변식.
- **개발:** width/{widthdata.txt,table.go(생성),width.go,truncate.go}, tools/gen_width/main.go, Makefile gen-width
- **검증:** go test 전 패키지 통과, go vet 무경고, 생성기 두 번 돌려 md5 동일(결정론)
- **비고:** 모호(A) 부류는 1칸으로 결정 — 박스 문자가 여기 속해 2칸으로 보면 상자가 두 배가 된다.

### [2026-09-07 01:59] 보리차 2단계 — input 입력 파서(바이트 → 사건)
- **기획:** 터미널 입력은 바이트로만 온다. CSI/SS3 문법을 상태 기계로 옮겨 키·마우스·붙여넣기·포커스로 바꾸는 층. tea 가 input 을 쓰는 방향이라 순환을 피해 input 을 먼저 만듦(PLAN §8 순서 변경, 로그에 기록).
- **TC:** 바이트→사건 대응표 70여 건(한글·이모지·조합키·SGR 마우스·붙여넣기), 같은 입력을 **모든 바이트 경계에서 잘라** 결과 동일 검증, 한 바이트씩 흘려넣기, 반쪽 UTF-8 대기·깨진 UTF-8 폐기, ESC 단독→Flush, 붙여넣기 중 Flush 무시, Reader 시계 4종.
- **개발:** input/{keys,decoder,mouse,paste,reader}.go + 테스트 3개
- **검증:** go test 통과(input·term), go vet 무경고, 교차 컴파일 유지, 누적 2,302줄
- **비고:** android/arm64 는 -race 미지원 — 경합 검증은 설계와 타이밍 테스트로 대신함.

### [2026-09-07 01:47] 보리차 1단계 — 모듈·Makefile·term 드라이버·날것 터미널 예제
- **기획:** boricha/PLAN.md의 §8 커밋 1. Bubble Tea 같은 TUI 프레임워크를 표준 라이브러리만으로 바닥부터. 첫 층은 터미널 드라이버와 "프레임워크 없이 해 보기" 데모.
- **TC:** 시퀀스 바이트 대조 21종, CursorTo/Up/Down/ToCol 경계값(0·음수), Cleanup 역순·멱등·켠 것만 되돌리기, MakeRaw 비트 산술(가짜 Termios 전비트 1), 무관 필드 보존, winsize 0×0 거부, 비터미널 오류.
- **개발:** boricha/go.mod, Makefile, term/{seq,term,term_unix,term_windows,termios_unix,termios_linux,termios_darwin}.go, examples/00_raw/main.go 외 3개 파일
- **검증:** go test 통과(term ok), go vet 무경고, GOOS=darwin/windows 교차 컴파일 성공, tmux 80×24 실캡처 out/tmux_00_raw.txt(방향키 = 1B 5B 44)
- **비고:** macOS termios 경로는 컴파일만 확인, 실행 미검증. 덱 조립은 §8 커밋 10부터.

### [2026-09-07 10:06] template.html 고정폭 글꼴(DeckMono) 내장과 tools/embed_mono_font.py
- **기획:** template 계열 덱이 Consolas·SF Mono를 앞세워 한글·박스 문자가 다른 글꼴로 빠지며 아스키 표가 깨짐. Bubble Tea 덱에서 검증한 D2Coding 서브셋 내장을 공용 스크립트로 일반화.
- **TC:** 고정폭 요소 글자 수집·엔티티 복원, ASCII·박스 항상 포함, 반각 500/전각 1000 폭 계약과 위반 감지, 이모지 경고, 삽입·제자리 교체·두 번 돌려도 동일·저장 시각 미기록·CRLF 보존·style 없음, check 4종 (19건).
- **개발:** tools/embed_mono_font.py, tools/test_embed_mono_font.py, template.html(고정폭 목록 17곳 통일·글꼴 21KB·글꼴 슬라이드 1장·사용법·점검·함정표), CLAUDE.md
- **검증:** 19 passed, 0 failed · template.html --check 통과 · Go_Bubble_Tea 덱 --check 통과 · 태그 균형 확인
- **비고:** 기존 template 계열 문서 20개는 후속 작업으로 같은 스크립트를 일괄 적용 예정. Playwright를 못 쓰는 환경이라 브라우저 렌더링은 눈으로 확인하지 못함.
