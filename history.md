### [2026-09-12 19:35] 부록 표지의 파일 수·줄 수를 조립기가 채우게
- **기획:** 3차 리뷰에서 이 숫자가 실제로 한 줄 어긋났다(tools 를 한 줄 고치자 부록 표지가 옛 수를 말했다). 손으로 적는 한 또 어긋나므로 `<!--SRCSTAT ...-->` 표식을 두고 조립기가 세게 했다.
- **TC:** `tools/width.py` 에 두 줄을 붙였다 놓고 `make deck` — 표지가 23,915 → 23,917 로 따라갔다(RED→GREEN). 되돌린 뒤 다시 23,915.
- **개발:** `deck/build_deck.py`(SRCSTAT 확장 · 절 표지는 다음 표식까지의 FULLSRC 를 센다) · `deck/gen_appendix.py`(생성기도 같은 표식을 낸다) · `deck/sections/{14,15}`.
- **검증:** `make all` 오류 0건 · 1,478장 · 부록 연속성 143파일 0건 · 파이썬 249 passed, 0 failed.
- **비고:** 총계는 부록에 실리는 143개 파일의 줄 합이다. 커버리지가 세는 23,369줄(시험·도구를 뺀 값)과는 다른 수다.

### [2026-09-12 19:10] 압축 덱 3차 리뷰 — 부록 770장, 사실오류 4건·화살표 4건·표기 7건 정정
- **기획:** 2차는 본문만 정독했다. 3차는 부록(용어집 137·참고문헌 4·소스 전문 143파일)을 대상으로, 부록이 스스로 주장하는 것(연속성·조각 번호·"주석은 전부 한국어")을 기계로 검사한 뒤 용어집과 소스 주석을 읽었다.
- **TC:** `scratch/review2/{check_appendix,check_glossary}.py` — 파일마다 부록 조각이 1..N 을 빈틈 없이 잇는가(조립기의 커버리지는 본문 인용이 메워도 100% 다), 조각 제목의 이름이 그 코드에 있는가, 용어집 화살표가 그 낱말이 나오는 자리인가. 전부 RED→GREEN.
- **개발:** `deck/glossary.txt` · `deck/sections/{00,14,15}` · `src/py/compresslib/{cm,bwt}.py` · `src/{go,cpp,ts,java}` 의 bwt 머리말.
- **검증:** 부록 연속성 143파일 0건 · 조각 제목 708개 0건 · `make all` 오류 0건 · 파이썬 249 passed 0 failed · 골든 195쌍 0건 · 글꼴 `--check` 통과.
- **비고:** 부록 소스 주석도 덱 본문이다 — cm.py 머리말이 "APM 하나"(실제 둘)와 "덱은 모델 1~5개 비율을 보인다"(그런 화면 없음)를 적고 있었다. 2차에서 고친 "아홉 칸"도 주석에 그대로 남아 있었다.

### [2026-09-12 18:20] 압축 덱 2차 전수 리뷰 — 사실오류 8종·숫자 어긋남 5건·표기 6건 정정
- **기획:** 1차가 "덱↔저장소를 기계로 대조한 검사만 값을 했다" 고 남겼으므로, 2차는 1차에 없던 대조를 새로 짜고(산문 숫자↔golden·out, 용어 흔들림, 연도·RFC) 본문 5,679줄을 정독했다.
- **TC:** `scratch/review2/{extract,check_numbers}.py` — 산문의 1000 이상 숫자를 out/·golden/ 전문과 대조(남은 216건은 연도·서사로 전수 확인), 용어 짝 15종·괄호·중복 어절·U+FFFD 검사. 정정 전 RED.
- **개발:** `deck/sections/{00,01,02,05,06,07,09,10,11,12,13,14}` · `deck/gen_figs.py` · `deck/glossary.txt` · `tools/gen_tables.py` · `index.html` · `README.md`.
- **검증:** `make all` 오류 0건 · 1,478장 유지 · 파이썬 249 passed, 0 failed · `make width` 159파일 0건 · 글꼴 `--check` 통과.
- **비고:** 가장 큰 것은 intcode 골든 코덱을 "네 부호를 다 쓴다" 고 적은 자리 — 코드는 감마 하나뿐이고, 그 코드가 같은 화면에 인용돼 있었다. ANS 정규화의 "반올림"(실제는 내림), 도해의 부 번호, deflate 레벨 0 크기도 같은 종류다.

### [2026-09-12 17:35] 압축 대백과사전 — 17모듈 × 5언어, 1,478장 완성
- **기획:** PLAN.md §5 의 14단계를 1~14 전부 수행. 압축 알고리즘 17개를 Python·Go·C++·Java·TypeScript 로 각각 구현하고 **부호기 출력 바이트가 완전히 같음**을 골든 195쌍 + 5×5 교차 복호로 증명하는 덱.
- **TC:** 파이썬 249개 + 네 언어 시험, 골든 15모듈×13파일, 교차 복호 모듈마다 175건, 복호기 전용 2모듈은 진짜 bzip2·xz 파일 130건, 진짜 zlib·gzip·lz4 와 양방향 interop.
- **개발:** `compress/src/{py,cpp,go,ts,java}` · `cli/` · `bench/` · `interop/` · `tools/` · `deck/` 외 142개 파일 23,000여 줄. 덱 본문 708장 + 부록 770장.
- **검증:** `make all` 오류 0건 · 슬라이드 1,478장 · 소스 커버리지 100% · 파서티 전 모듈 실패 0건 · 데모 동작 16건 · 인용 범위 어긋남 0건.
- **비고:** 왕복이 멀쩡한 채로 틀린 버그가 셋 나왔다(CM 학습률·APM 곱수, BWT 정렬 키). 크기와 교과서 기댓값만이 잡았다. 전수 리뷰 1차에서 구조 3·사실오류 2·인용범위 1·표기 7건 정정.

### [2026-09-12 15:46] 덱 5개 꼬리 주석 열 정렬 정정 (5블록)
- **기획:** DeckMono 를 실어 칸이 확정되자 드러난 어긋남. 앞선 "마지막 2칸 공백" 감지는 오탐이 많아(문자열 속 공백·`d  =`) 꼬리 주석 표식(`//`·`--`) 의 칸 위치로 판정을 바꿨다 — 17블록 중 실제 어긋남은 5블록.
- **TC:** `check_comment_cols.py`(scratch) — 주석줄 3개 이상에서 칸 최빈값에 2/3 이상 모이면 정렬 의도로 보고 벗어난 줄을 잡는다. 폭은 D2Coding 실측(①류 전각). 수정 전 5블록(RED) → 후 0건.
- **개발:** `Go_기초`·`TypeScript_기초`(넘친 1칸 당김) · `boricha/deck/sections/11_apps.html`(2칸, `make deck` 재조립) · `모던_C++의_진화`·`자바의_진화`(긴 줄에 열을 맞춰 넓힘). 공백 길이만 바꿨다.
- **검증:** 열 검사 0건 · 글꼴 `--check` 5개 통과 · 인코딩·줄바꿈 보존 · 세 블록을 rsvg 로 렌더해 주석 x 좌표 일치를 눈으로 확인. 블록 폭은 모던_C++ 71칸 그대로, 자바의_진화 69→72칸(overflow-x:auto 라 잘리지 않음).
- **비고:** `러브2D_아웃런` 2블록은 애초에 꼬리 주석 열을 쓰지 않는다(①~④ 열이 42·49·46·47) — 강제로 맞추면 없던 서식을 만드는 셈이라 제외했다. `자바의_진화` 고정폭에 기존 U+FFFD 1자가 그대로 있다.

### [2026-09-12 15:33] 덱 91개에 DeckMono 글꼴 일괄 내장 (+3.0 MB)
- **기획:** 남은 미내장 문서를 전수 조사해 대상을 갈랐다. 고정폭 요소가 없는 6개(index·art 등)와 갱신마다 서브셋이 낡는 `history.html` 은 제외. 목록을 CSS 변수로 둔 2개(red-phone·오목)는 변수 정의 쪽을 고쳤다.
- **TC:** 자동 검증 4종 — `--check` 전수 · 인코딩·줄바꿈·U+FFFD 보존 · 글꼴 외 변경 0 · 재실행 바이트 멱등. 아울러 폭이 어긋나는 글자(①류)가 든 34블록을 1칸/2칸 두 가정으로 재어 그림이 밀리는지 검사.
- **개발:** `bulk_embed.py`(scratch, 미커밋)로 고정폭 글꼴 목록 앞에 DeckMono 를 세우고 서브셋 @font-face 삽입 — 91개 파일. 목록 평균 9곳/덱.
- **검증:** 91개 전부 `--check` 통과 · 어긋남 0 · 멱등 10/10 · **1칸 가정에서만 맞는 블록 0개**(깨지는 그림 없음) · 표 정렬은 두 덱을 rsvg 로 렌더해 눈으로 확인. 40.7 MB → 43.7 MB, 덱당 평균 +33 KB.
- **비고:** ①류가 든 15블록은 1칸·2칸 어느 쪽에서도 열이 안 맞는다(글꼴과 무관한 기존 결함, 대부분 번호 목록이라 정렬 의도가 없어 보임) — 손대지 않았다. `자바의_진화.html` 고정폭에 U+FFFD 1자가 기존에 있다.

### [2026-09-12 15:20] C++ WASM 테트리스 덱 — DeckMono 글꼴 내장 (35 KB)
- **기획:** 폰·태블릿엔 한글 고정폭 글꼴이 없어 아스키 표가 어긋난다. 라이선스는 D2Coding SIL OFL 1.1 로 서브셋·웹내장 허용, Reserved Font Name 은 `DeckMono` 개명으로 충족.
- **TC:** 모호(A) 폭 계약 시험 4종을 `tools/test_embed_mono_font.py` 에 추가(RED 3건) — 내장 도구가 ① 에서 죽던 것이 원인이었다. 23 tests OK.
- **개발:** `tools/embed_mono_font.py`(모호는 경고, 그 외는 중단 — boricha 에서 백포트) · `C++_WASM_테트리스_만들기.html`(고정폭 목록 5곳에 DeckMono 앞세움 + @font-face, T스핀 조건 블록 괄호 열 2칸 정정)
- **검증:** `--check` 통과 · 재실행 바이트 멱등 · 기존 내장 덱 2개 회귀 없음 · 내장 서브셋 metrics 로 괄호 열 25.000em 일치 확인 후 rsvg 렌더로 눈으로 재확인. 471 KB → 520 KB.
- **비고:** 같은 벽에 막혀 있던 덱이 21개 더 있다(AI처럼_디버깅하기 ①~⑳ 184회 등) — 일괄 내장은 별 작업.

### [2026-09-12 15:10] C++ WASM 테트리스 덱 — 쪼개진 `&#x27;` 엔티티 11곳 정정
- **기획:** 5장 `echo &#x27...` 신고에서 출발. 문법 강조기가 `&#x27;` 의 `#` 을 셸/JS 주석 시작으로 오인해 `&` 와 `#x27;` 사이에 `<i class="cm">` 을 끼워 넣어, 엔티티가 깨져 따옴표가 글자 그대로 노출되고 뒤 전체가 주석 색으로 칠해졌다.
- **TC:** 검사기 먼저 — `&<태그>#x27;` 패턴과 코드 줄의 `<i>`/`</i>` 균형을 본다. 수정 전 11줄 검출(RED).
- **개발:** `C++_WASM_테트리스_만들기.html` — 끼어든 열기 태그와 짝 닫기 태그만 제거(419·3424~3426·3429·4887~4889·4967~4969). 삽입 11줄 · 삭제 11줄.
- **검증:** 검사기 0건. 11줄 렌더 텍스트를 눈으로 확인. 5장 명령은 실제로 돌려 `t.wasm` 생성 확인. UTF-8·LF·U+FFFD 0 유지.
- **비고:** 이 덱은 DeckMono 글꼴 미내장(`--check` 어긋남 2건) — 별 작업. 5장 예시 출력 `564 t.wasm` 은 clang 판에 따라 달라지는 예시라 손대지 않았다.

### [2026-09-12 10:18] 압축 대백과사전 — 1단계 뼈대 (덱 20장, make all 통과)
- **기획:** PLAN.md §5 1단계. 조립기·검사기를 keycloak_ad 에서 물려받아 이 덱에 맞췄다. 덱은 산출물, 소스가 원본이라는 규율을 처음부터 기계로 건다.
- **TC:** 검사기 자체가 시험이다 — deck-verify(역검증)·deck-slices(인용 경계)·deck-xref(상호참조)·deck-check(DOM 스텁)·font-check·width 를 전부 돌려 통과 확인.
- **개발:** compress/Makefile · deck/build_deck.py · deck/chunks.py(C++·Java·TS 경계 추가) · deck/check_slices.py · deck/base/head.html(제목·다섯 언어 배색) · deck/sections/*.html 16개 · tools/flock_java.sh 외 6개 파일
- **검증:** SKEL=1 make all 오류 0건 · 슬라이드 20장 · 예상 합계 2,260장(상한 3000) · 글꼴 433자 27 KB 내장
- **비고:** 소스·코퍼스는 아직 0줄이라 커버리지 0%. index/README 등록은 PLAN §5 13단계까지 하지 않는다. 다음은 2단계 SPEC.md.

### [2026-09-09 07:50] Keycloak×AD 덱 — 가짜 AD 바인드 순서를 진짜 AD 와 맞추고 "지운 사람" 실험 캡처 추가
- **기획:** 2차 리뷰가 글로만 적었던 둘을 코드·캡처로. Bind 순서(잠김→비밀번호→꺼짐), AD 에서 지운 사용자가 다음 조회 때 사본이 지워지는 실험.
- **TC:** 꺼짐+틀린 비밀번호 → 52e · LDIF 다시 읽기 뒤 항목·memberOf 사라짐(fakead 2건). 첫 실행은 같은 파일의 다른 시험 때문에 빌드 실패라 52e 만의 RED 는 못 봤다.
- **개발:** ldap/fakead/dir.go · ldap/fakead/cmd/fakead/main.go(SIGHUP 재읽기) · keycloak/ad_lab.sh(실험 7) · tools/record.sh · deck/sections 03·05·07 · deck/claims.md · index.html · README.md 외 30개 캡처
- **검증:** make all 0건(1009장 · 커버리지 9140/9140 · 인용 범위 285개 · 데모 17건) · go test 14패키지 · vet · record.sh 전체 1회(kc_ 아닌 캡처는 커밋본과 동일)
- **비고:** 실험 결과 objectGUID 검색 0건 → 사본 삭제 → 목록 7명→6명. 부록 전문이 늘어 1009장이 됐다.

### [2026-09-09 05:55] Keycloak×AD 덱 2차 리뷰 — 사실오류 17건·모순 34건·인용범위 84건·퀴즈 7건·표기 14건·레이아웃 3건·데모 4건 정정
- **기획:** PLAN §8 15단계. 0~4부·5~13부를 서브에이전트 둘이 소스·캡처·RFC 와 대조, 데모·숫자 정합은 직접 검토.
- **TC:** deck/check_slices.py(인용 범위 경계) 59건 RED · check_deck.js 8·9단계(데모 동작) 5건 RED → 전부 GREEN.
- **개발:** k8s/base/keycloak.yaml · deck/sections 00~13 · deck/demos.js · deck/check_slices.py · Makefile · deck/claims.md · index.html · README.md 외 12개 파일
- **검증:** make all 0건(1005장 · 커버리지 9015/9015 · 인용 범위 285개) · go test 14패키지 · vet
- **비고:** 공식 이미지에 --optimized 를 붙이면 build 옵션이 무시돼 프로브가 죽는다. k8s 캡처 넷은 오프라인 재기록.

### [2026-09-09 04:46] index·README 목록 정합 — 카드 1건·항목 43건 보강
- **기획:** 디스크 문서 ↔ index 카드 ↔ README 항목을 3방향 대조해 누락만 채운다. 기존 항목의 순서·문구는 건드리지 않는다.
- **TC:** verify_index.py — 누락·역누락·링크 실체·앵커 대상을 한 번에 검사. 첫 실행 45건 실패(RED).
- **개발:** index.html(자격증 섹션 신설 + 빠른 이동 1줄) · README.md(C 언어 시리즈·언어 만들기 섹션 신설, 항목 43건 추가)
- **검증:** 불일치 0건 · README 구조 이탈 0건 · index.html 파싱 통과 · 삽입 61줄 / 삭제 0줄
- **비고:** README 는 .md 원본을, index 는 .html 을 가리키는 항목이 섞여 있어 비교 키는 확장자를 뗀 stem 으로 잡았다. 게임 항목 12건은 기존 순서를 흩지 않으려 섹션 끝에 모아 붙였다.

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

---
## Archive
- [2026-09](history/archive/history-2026-09.md) — 25 entries
