### [2026-10-12 04:49] Rust 덱 확장 뼈대 — 새 부 10개(17~26부) 계약·예산, 부록은 27로
- **기획:** 사용자 승인(약 1,890장까지). 17~23부 표준 라이브러리와 심화, 24~26부 실전(프로젝트·연습 문제·오류 처방전), 0~16부 보강. 부록을 17 → 27로 옮겨 번호를 비웠다.
- **TC:** 정상(부록 id 가 p27 로 바뀌어도 덱 안 상호참조가 모두 실재) / 경계(뼈대만 있는 부는 order.txt 에서 주석 — 뼈대 없이 조립이 통과).
- **개발:** `rust/deck/OUTLINE.md`, `rust/deck/budget.txt`, `rust/deck/order.txt`, `rust/deck/AUTHORING.md`, `rust/PLAN.md`, `rust/deck/sections/27_appendix.html`, `rust/ex/27`, `rust/out/27` 외 뼈대 18개 파일
- **검증:** 104 passed, 0 failed · make all 922장 오류 0건 · 역검증 어긋남 0건
- **비고:** 아직 새 내용은 없다(922장 그대로). 집필은 부마다 에이전트 하나씩 차례로.

### [2026-10-12 01:11] Rust 기초 문법집 덱 상한을 2000장으로
- **기획:** 사용자 결정으로 전체 장수 상한을 1000 → 2000장으로 올린다. 부별 목표(합계 945)는 늘릴 계획이 정해질 때까지 그대로 둔다.
- **TC:** 정상(2000장 초과는 "상한은 2000장" 오류) / 경계(옛 상한 1000장을 넘는 1002장은 상한 오류가 없어야 한다).
- **개발:** `rust/deck/build_deck.py`, `rust/tools/tests/test_build_deck.py`, `rust/deck/budget.txt`, `rust/deck/OUTLINE.md`, `rust/PLAN.md`
- **검증:** 104 passed, 0 failed · make deck 922장 오류 0건
- **비고:** 부별 예산(+10 %)이 그대로라 지금은 어느 부도 더 늘릴 수 없다. 확장 계획 승인 뒤 `budget.txt` 를 고친다.

### [2026-10-11 23:05] Rust 기초 문법집 덱 리뷰 2 — 독자 흐름·문체, 922장
- **기획:** 사실·증거를 본 리뷰 1에 이어, 전 부를 처음부터 끝까지 이어 읽으며 흐름·중복·용어·문체를 맞췄다. 기준표(`REVIEW2.md`)를 먼저 세우고 13묶음을 리뷰어 하나씩 차례로 돌렸다.
- **TC:** 정상(뒤 부가 앞 부의 슬라이드를 한 구절과 링크로 이어 받는다) / 경계(명령 줄을 빼고 센 "출력 N번째 줄", 캡처가 증명하지 못하는 문장, 출처가 달린 1부 문장의 뜻 보존).
- **개발:** `rust/deck/sections/*.html`, `rust/deck/REVIEW2.md`, `rust/deck/glossary.tsv`, `rust/data/features.tsv`, `rust/ex/04/match_bind.rs`, `rust/ex/08/str_methods.rs`, `rust/PLAN.md`, `Rust_기초_문법집.html` 외 `index.html`·`README.md`·예제 주석 14개 파일
- **검증:** 103 passed, 0 failed · make all 오류 0건 · 역검증 블록 1,254개 어긋남 0건 · 예제 621개 전수 재실행 3회 모두 621 일치·0 불일치
- **비고:** 정정 약 1,570건(링크·시제 410·흐름 283·중복 239·용어 234·콜아웃 180). 표 1장 추가(921→922), 용어집 59→64낱말. 목차에만 있고 슬라이드가 없는 항목 8건은 장수 때문에 그대로 둠(`rust/PLAN.md`).

### [2026-10-11 17:11] Rust 기초 문법집 덱 리뷰 1 — 전 부 정독, 921장
- **기획:** 0~16부와 부록을 부별로 리뷰어 하나씩(동시에 하나만) 맡겨, 본문·예제·캡처 셋의 일치와 앞뒤 순서·근거를 대조하고 그 자리에서 고치게 했다.
- **TC:** 정상(오류 슬라이드가 그 메시지를 줄 번호와 함께 읽는다) / 경계(시험 여러 개의 결과 줄 순서, 따옴표·`>` 로 시작하는 설명, 파일 위쪽을 자른 인용의 줄 번호, 출처 문장보다 더 말하는 번역).
- **개발:** `rust/deck/sections/*.html`, `rust/ex/**`, `rust/out/**`, `rust/data/facts.tsv`, `rust/data/features.tsv`, `rust/deck/glossary.tsv`, `rust/deck/build_deck.py`, `rust/tools/rsrun.py` 외 `index.html`·`README.md`·`Rust_기초_문법집.html`
- **검증:** 103 passed, 0 failed · make all 오류 0건 · 역검증 블록 1,254개 어긋남 0건 · 예제 621개 전수 재실행 3회 모두 621 일치·0 불일치
- **비고:** 정정 약 620건(미설명·증거불일치·순서·근거없음·절단이 대부분, 1부는 출처초과 45). 근거 슬라이드 9장 추가(912→921). 흔들리던 다중 시험 예제 4개는 한 스레드로 고정. GC 제거 시점은 출처끼리 달라 둘 다 적어 둠.

### [2026-10-11 12:48] Rust 기초 문법집 덱 완성 — 18부 912장
- **기획:** 역사(1부)와 기초 문법 전부(2~16부)·부록. 상한 1000장, 표준 라이브러리만, 돌린 예제만. 집필 에이전트는 한 번에 하나만 쓰고 나머지 부는 병행해 직접 썼다.
- **TC:** 정상(예제 610개의 실행·기대한 컴파일 오류·종료 코드) / 경계(`>` 가 든 지시자 설명, 블록 중간에서 끊긴 인용, 문서 시험의 걸린 시간, 번호 없는 문법 오류).
- **개발:** `rust/deck/sections/*.html`, `rust/ex/**`, `rust/out/**`, `rust/data/*.tsv`, `rust/deck/build_deck.py`, `rust/tools/*.py`, `Rust_기초_문법집.html`, `index.html` 외 `README.md`
- **검증:** 98 passed, 0 failed · make all(SKEL 없이) 오류 0건 · 역검증 블록 1,233개 어긋남 0건 · 글꼴 내장 통과
- **비고:** 설명에 `>` 가 든 지시자가 조용히 빠지던 조립기 결함을 회귀 시험과 함께 고침(8장 복구). 리뷰 1차는 부별로 진행 중(2·3부 8건 정정 반영).

### [2026-10-11 11:09] Rust 기초 문법집 덱 — 뼈대와 조립 도구
- **기획:** template.html 을 head·tail 로 갈라 빌드형 덱으로 만든다. 상한 1000장, 표준 라이브러리만, 예제는 전부 실제 rustc 1.99.0 으로 돌린 것만 싣는다(rust/PLAN.md).
- **TC:** 정상(지시자 해석·명령 줄·캡처 형식·RUN/CODE/OUT 펼치기) / 경계(가운데 지시자, 기대와 다른 오류 코드·종료 코드, 무한 루프 시간 초과, 낡은 캡처, 72칸·45줄·1000장 초과, 손으로 쓴 pre).
- **개발:** `rust/tools/rsrun.py`, `rust/deck/build_deck.py`, `rust/deck/verify_deck.py`, `rust/deck/check_deck.js`, `rust/deck/base/*.html`, `rust/Makefile`, `rust/PLAN.md`, `.gitignore` 외 조각 18개
- **검증:** 65 passed, 0 failed · make all SKEL=1 오류 0건(19장)
- **비고:** 본문은 아직 플레이스홀더. 하이라이터에 Rust 수명·날 문자열·속성 처리를 더했다(덱의 tail.html 한정).

### [2026-10-09 08:48] C#의 진화 예제 폴더의 빌드 산출물 정리 — bin/ 129개 파일 추적 해제
- **기획:** 7부 작성 때 예제 폴더 안에서 csrun 을 직접 돌려 생긴 bin/(a.dll·a.pdb·a.rc.json) 43곳이 커밋돼 있던 것을 뺌.
- **TC:** 정상(덱 빌드·역검증이 bin/ 없이 통과) / 경계(다시 생겨도 .gitignore 가 막는다).
- **개발:** `.gitignore`, `csevo/ex/07/*/bin/` 외 128개 파일 삭제
- **검증:** build_deck 오류 0건 · deck-verify 역검증 통과 · 글꼴 내장 뒤 덱 HTML 이 커밋된 판과 동일

### [2026-10-08 23:57] C#의 진화 덱 리뷰 3(정밀 대조) — 결함 140건 정정
- **기획:** 코드·캡처·본문 셋의 일치, 근거 없는 단정의 실측, 부 사이 모순·시효, 리뷰 2 치환 부작용을 리뷰어 12명이 6라운드로 점검.
- **TC:** 정상(캡처가 본문 주장을 뒷받침) / 경계(7.2→7.3 에서 깨지는 오버로드, 참조 팩과 런타임의 차이, 하나뿐인 `_` 매개변수).
- **개발:** `csevo/deck/sections/*.html`, `csevo/deck/glossary/*.txt`, `csevo/ex/08/v73ovlbreak`·`v73unmmodreq`(새 예제), `csevo/tools/csrun`, `csevo/exps/p08c.py`·`p13b.py`·`p15b.py`, `csevo/data/features/*.tsv`, `index.html`, `README.md` 외 다수
- **검증:** 시험 128 passed · make all 오류 0건 · 예제 1,994개 경고 0 · p08c 캡처 두 번 동일
- **비고:** 증거불일치 55·사실오류 39·표기 20·시효 9·모순 8·링크 7·퀴즈 2. record.sh --check(전체 두 번 재실행)는 시간 탓에 미실행.

### [2026-10-08 16:52] C#의 진화 덱 출처 표시 이름 정리 — 역사 문서 21건
- **기획:** 부록 출처 목록·배지에서 Computerworld 7쪽이 같은 이름이고 artima·"- Source" 꼬리, 파일 이름이 그대로 보이던 것을 생성 단계에서 다듬음.
- **TC:** 정상(Artima·보도자료·Learn 꼬리 떼기) / 경계(쪽마다 같은 제목 → N/전체쪽, <title> 없는 옛 문서 2건).
- **개발:** `csevo/tools/make_data.py`, `csevo/tools/tests/test_make_data.py`, `csevo/data/cite_keys.tsv`, `CSharp의_진화.html` 외 3개 파일
- **검증:** 시험 128 passed · make all 오류 0건

### [2026-10-08 16:46] C#의 진화 덱 리뷰 2(독자 흐름) — 결함 260건 정정, 용어 통일
- **기획:** 0~17부를 한 독자로 순서대로 읽어 흐름·용어·퀴즈·문체·링크를 점검(리뷰어 둘씩 4라운드, 세션 두 번 끊겨 재개).
- **TC:** 정상(장 퀴즈가 앞 슬라이드로 풀리는지) / 경계(멀리 가리키는 "앞 장", 이중 이스케이프, 생성 표 속 옛 용어).
- **개발:** `csevo/deck/sections/*.html`, `csevo/deck/glossary/*.txt`, `csevo/deck/build_deck.py`, `csevo/tools/make_data.py`, `csevo/exps/p13b.py`·`p14c.py`·`p15b.py`, `index.html`, `README.md` 외 다수
- **검증:** 시험 127 passed · make all 오류 0건 · 2,759장·캡처 3,373개·예제 1,992개 경고 0
- **비고:** 2부 정리·퀴즈·다리 3장 추가, 용어집 461→441낱말. 리뷰 1 은 767bd5e. p17 출처 표시 이름 정리는 남음.

### [2026-10-08 02:41] C#의 진화 덱 완성 — 0~16부·부록 2,759장, 카드 추가
- **기획:** 끊긴 세션을 이어 16부(p16·p16b 재개)·1부·부록을 서브에이전트 둘씩 병행해 채움. 부록 예산은 용어집 51장 때문에 60→100(사용자 승인).
- **TC:** 정상(langversion 사다리·다섯 시대·Java 21 대조 캡처 두 번 동일) / 경계(1차 출처 없는 COOL 날짜는 미확인, 200칸 넘는 진단 줄, 용어집 중복).
- **개발:** `csevo/deck/sections/01_origins.html`, `16_flows.html`, `16b_flows.html`, `17_appendix.html`, `csevo/deck/gen_tables.py`, `csevo/tools/fetch_docs.py`, `index.html`, `README.md` 외 다수
- **검증:** 시험 124 passed · make all(SKEL 없이) 오류 0건 · 예제 1,992개 경고 0
- **비고:** 16부 564d6ad·1부/부록 f791fcc push. 리뷰 1·2차 남음(.NET 9 GA 날짜 2024-12-03 오기 등 review_todo).

### [2026-09-25 09:09] Go의 진화 덱 리뷰 1·2 — 결함 85건 정정(756장)
- **기획:** 1차는 전 부의 날짜·버전·수치를 docs/ 와 캡처에 대조, 2차는 초보 독자 흐름·3–5부 정밀 재대조·형제 덱 중복.
- **TC:** 정상(인용 절이 문장을 뒷받침) / 경계(캐시가 돌려준 남의 경로가 든 vet 캡처, 팀 이름 저자, 초안 판).
- **개발:** `goevo/deck/sections/*.html`, `goevo/tools/gover.py`, `goevo/deck/gen_tables.py`, `goevo/deck/glossary/p00.txt`, `goevo/ex/06/stack/main.go`, `index.html`, `README.md`
- **검증:** 시험 132 passed · make all 오류 0건 · 데모 16건 통과
- **비고:** 1차 fbac426(28건), 2차 4d6ce22(57건). push 전 record.sh --check(세 번 실행) 남음.

### [2026-09-25 07:57] Go의 진화 덱 완성 — 6·7·8·10부와 데모, 755장
- **기획:** 끊긴 세션을 이어받아 남은 6·7·8·10부를 채우고 데모·카드를 붙임. 8부(1.25–1.27)는 세 파일로 나눠 서브에이전트 둘과 병행.
- **TC:** 정상(부 합산 예산·흐름 표·데모 자료 생성) / 경계(쪼갠 부의 장 번호, 캐시가 돌려준 남의 경로, 초안 1.28 제외, 없는 설정·판 입력).
- **개발:** `goevo/deck/sections/0[6-8]*.html`, `goevo/deck/sections/10_flows.html`, `goevo/deck/gen_demos.py`, `goevo/deck/gen_tables.py`, `goevo/tools/gover.py`, `goevo/deck/check_xref.py`, `index.html`, `README.md` 외 다수
- **검증:** 시험 130 passed · make all(SKEL 없이) 오류 0건 · 8·10부 캡처 175개 두 번 돌려 동일
- **비고:** 755장은 목표 띠(820–960)보다 적다(채우려 늘리지 않음). 리뷰 1·2차는 아직.

### [2026-09-25 06:10] 드론의 모든 것 덱 5부 9장 — 만원대 장난감 드론의 6축 상보 필터(16장)
- **기획:** 사용자 요청. 완구 H8 mini 의 오픈소스 수평 펌웨어(MIT) 소스를 근거로, 6축만으로 기울기를 잡는 상보 필터와 헤드리스 모드의 표류를 해부.
- **TC:** 정상(수평 유지·자이로 적분·시간 상수 e⁻¹) / 경계(가속도 창 0.7·1.3 g 제외, dt·T ≤ 0, 요 ±π 감기, 기운 채 가속하는 착시).
- **개발:** `drone/ex/toy_imu.py`, `drone/ex/tests/test_p05_toy.py`, `drone/exps/p05.py`, `drone/deck/sections/05_sensors.html`, `drone/data/cite_keys.tsv`, `drone/data/excerpts/`, `index.html`, `README.md`
- **검증:** toy 시험 13 passed · make all(SKEL 없이) 오류 0건 · 20초 정상 오차가 T23 의 b·T 와 둘째 자리까지 일치
- **비고:** 바이어스 크기는 덱의 센서 모델 가정(sigma_bg) — 실제 칩과 다름을 슬라이드에 밝힘.

### [2026-09-25 05:10] 드론의 모든 것 덱 리뷰 1·2·3 — 사실·증명·읽기 흐름 정정
- **기획:** 완성본을 세 갈래로 점검 — 인용한 문장마다 원문 절 대조(서브에이전트), 완전 증명 70개 점검표, 1학년 독자로 7–10·14–16부 정독.
- **TC:** 정상(인용 절·증인 시험·연습 문제 재계산) / 경계(자료 갱신 뒤 낡은 수, 부 번호 오참조, 기네스 미확인 기록).
- **개발:** `drone/deck/sections/*.html`, `drone/data/shows.tsv`, `drone/data/timeline.tsv`, `drone/exps/p14.py`, `drone/SPEC.md`
- **검증:** make all(SKEL 없이) 오류 0건 · 사실 20건·증명 14건·읽기 흐름 11건 정정
- **비고:** 기네스 기록 사다리는 서로 다른 기록 이름을 잇는다(캡션에 밝힘). 글로벌 호크 첫 비행일 미확인.

### [2026-09-25 04:10] 드론의 모든 것 덱 완성 — 1,300장, make all 초록(SKEL 없이)
- **기획:** PLAN.md 의 19부(0–17부·부록)를 채움. 4·5·6부는 서브에이전트, 나머지는 직접. 정리 91개, 완전 증명 70개.
- **TC:** 정상(쇼 계획·점검·파리티·데모 6종) / 경계(곡선 간격 1.2d, T31 바닥 1.061 m, 고도 120 m, 비행시간 경계, zip 바이트 재현).
- **개발:** `drone/deck/sections/*.html`, `drone/py/droneshow/`, `drone/js/`, `drone/ex/`, `drone/exps/`, `drone/deck/gen_figs.py`, `index.html`, `README.md` 외 다수
- **검증:** tools 156 · py 225 · ex 141 · js 11 passed, 0 failed · make all 오류 0건
- **비고:** 곡선 점 배치 결함(하트 2배)·CSV 색 공간 차이 정정. 리뷰 1(사실)·3(읽기 흐름) 남음.

### [2026-09-25 00:16] 드론의 모든 것 덱 1단계 — 뼈대(27장, make all SKEL=1 초록)
- **기획:** goevo 조립기 계보를 물려받아 GOVER·REL 을 빼고 THM·WITNESS·SHOW 지시자와 정리 검사(thm-check)를 더함. 상한 3000장.
- **TC:** 31건 — 정상(정리 상자·증인 줄·SHOW 렌더) / 경계(심화 선행 정리, 없는 증인 시험, 증명 장 배지 0·2개, 쉼표 대수 1,218, 조문 제124조의2).
- **개발:** `drone/deck/build_deck.py`, `drone/deck/check_thm.py`, `drone/deck/check_claims.py`, `drone/deck/check_xref.py`, `drone/deck/cites.py`, `drone/deck/base/head.html`, `drone/Makefile` 외 34개 파일
- **검증:** tools 시험 31 passed, 0 failed · make all SKEL=1 오류 0건
- **비고:** 다음은 2단계(fetch_docs·html_text·pdf_text·excerpt).

### [2026-09-24 23:40] Go의 진화 덱 부록 — 생성 표만으로 31장(일정·API·GODEBUG·인물·출처)
- **기획:** 부록의 표를 전부 자료에서 생성 — 큰 릴리스 일정과 부 릴리스 수, API 증가, GODEBUG 설정, 블로그 저자 색인, 출처 종류별 수. 용어집·퀴즈 색인은 조립기가 펼침.
- **TC:** 6건 — 정상(부 릴리스 수·마지막 고침판, 저자 글 수·첫/끝 날짜) / 경계(Go 1 의 126 패키지 생략, 긴 표 14행씩 쪼개기, 'for the Go team' 꼬리 제거·3편 미만 제외).
- **개발:** `goevo/deck/gen_tables.py`, `goevo/tools/tests/test_appendix_tables.py`, `goevo/deck/sections/11_appendix.html`, `goevo/out/tbl_app_*.html`(12개)
- **검증:** 112 passed, 0 failed · 부록 조립·역검증·상호참조·주장·check_deck 통과
- **비고:** 제안 색인은 기억 없이 만들 출처가 없어 뺐다(인물 색인은 블로그 저자로 대신).

### [2026-09-24 23:22] Go의 진화 덱 5부 — Go 1.11–1.17 101장(서브에이전트, 캡처 98개)
- **기획:** 모듈의 탄생과 가지치기, 오류 감싸기, 비동기 선점, embed·io/fs, //go:build, 레지스터 ABI. 언어 버전 짝은 1.13·1.14·1.17 기능에서.
- **TC:** 캡처 98개(세 번 같음) — 정상(모듈·%w·embed 등) / 경계(go 1.12·1.13·1.16 으로 내리면 거절, 1.16 부터 빌드가 go.mod 를 안 고침, vet 경고 7종 exit≠0).
- **개발:** `goevo/deck/sections/05_go111_117.html`, `goevo/data/features/p05.tsv`, `goevo/exps/p05.py`, `goevo/ex/05/`(60개), `goevo/deck/claims/p05.md`, `goevo/deck/glossary/p05.txt` 외
- **검증:** 106 passed, 0 failed · 5부 조립·역검증·상호참조·주장·용어집 검사 통과(용어집 한 줄 칸 오류는 오케스트레이터가 고침)
- **비고:** 비동기 선점 전의 멈춤·checkptr·1.17 스택 트레이스 인자는 이 기계에서 결정적으로 재현되지 않아 노트 인용만.

### [2026-09-24 20:57] Go의 진화 덱 4부 — Go 1.5–1.10 85장(서브에이전트, 캡처 69개)
- **기획:** 자기 호스팅·동시 GC·vendor·HTTP/2·context·SSA·sort.Slice·타입 별칭·monotonic time·빌드 캐시. GC 멈춤의 역사는 ISMM 기조연설 문장을 그대로 인용.
- **TC:** 캡처 69개 — 정상(context 취소·하위 시험·경계 검사 제거 등) / 경계(go 1.8 에서 타입 별칭 거절, vet 경고 3종 exit≠0, http2client=0 GODEBUG 짝). 들여쓴 하위 시험 시간 가리기 시험 1건 추가.
- **개발:** `goevo/deck/sections/04_go15_110.html`, `goevo/data/features/p04.tsv`, `goevo/exps/p04.py`, `goevo/ex/04/`(43개), `goevo/deck/claims/p04.md`, `goevo/deck/glossary/p04.txt`, `goevo/tools/gover.py` 외
- **검증:** 106 passed, 0 failed · 4부 조립·역검증·자료·상호참조·주장·용어집 검사 통과
- **비고:** 예산 110장 중 85장(채우려고 늘리지 않음). 기조연설의 "2017년 3월" 과 1.8 출시일(2017-02-16)의 차이는 주장 대장에 기록.

### [2026-09-24 19:54] Go의 진화 덱 3부 — Go 1.1–1.4 55장(서브에이전트, 캡처 37개)
- **기획:** 1.1–1.4 는 언어 버전으로 막히지 않아 '1.27.1 에서의 동작 + 노트 배지' 로. 릴리스마다 장 표지·개관·퀴즈.
- **TC:** 캡처 37개 — 정상(메서드 값·3인덱스 슬라이스·-cover·TestMain·go generate 등) / 경계(상수 0 나눗셈·서로게이트·**T·internal 거절 등 6개 exit 1).
- **개발:** `goevo/deck/sections/03_go11_14.html`, `goevo/data/features/p03.tsv`, `goevo/exps/p03.py`, `goevo/ex/03/`(32개), `goevo/deck/claims/p03.md`, `goevo/deck/glossary/p03.txt` 외
- **검증:** 3부 조립·역검증·자료·상호참조·주장 검사 통과(오케스트레이터 재확인), 수치 3건 노트와 대조
- **비고:** 기능 64행 중 36행이 전용 장. 4부는 작업 중.

### [2026-09-24 19:42] Go의 진화 덱 6단계 시작 — 도해 2장(릴리스 주기·API 증가)·연표 126행
- **기획:** 자료만으로 그리는 도해 생성기(gen_figs)와 연표. API 증가 봉우리가 새 플랫폼의 syscall 상수임을 확인해 표·그림에서 갈라 보임.
- **TC:** 5건 — 정상(큰 릴리스마다 점 하나·판마다 막대 하나, syscall 몫) / 경계(범례 견본이 세어지지 않음, 초안 점 하나, 날짜 연분수).
- **개발:** `goevo/deck/gen_figs.py`, `goevo/tools/tests/test_gen_figs.py`, `goevo/tools/make_data.py`, `goevo/data/api_added.tsv`, `goevo/data/timeline.tsv`, `goevo/tools/make_timeline.py`, `goevo/deck/figs/`(2장), `goevo/deck/svgkit.py`
- **검증:** 105 passed, 0 failed · PNG 로 렌더해 눈으로 확인(겹침 2곳 고침)
- **비고:** 봉우리 1.1·1.13·1.14·1.16·1.20 은 syscall 이 대부분(6,329·3,885·4,251·3,570·4,289개).

### [2026-09-24 19:33] Go의 진화 덱 9부 — 1.28 초안과 Go 2 이야기 18장(캡처 6개)
- **기획:** Go 2 논의의 흐름(2017 문제 먼저 → 2018 초안·기준 → 2023 "깨는 Go 2 는 없다" → 2025 오류 문법 중단)과 tip 의 1.28 초안 노트.
- **TC:** 캡처 6개 — 1.28 을 요구하는 go.mod·1.28 API 는 1.27.1 이 거절(exit 1), 초안이 바꿀 지금의 동작(EncodedLen 음수·대문자 프록시 우선·vet 침묵). 시험 2건 추가(초안 개관 표, 소문자 환경 변수).
- **개발:** `goevo/deck/sections/09_go128_go2.html`, `goevo/data/features/p09.tsv`, `goevo/exps/p09.py`, `goevo/ex/09/`(5개), `goevo/deck/gen_tables.py`, `goevo/tools/gover.py` 외
- **검증:** 100 passed, 0 failed · 9부 조립·역검증·인용·주장 검사 통과
- **비고:** 1.28 은 초안(2026-09 기준). 정정: 앞선 '4단계 기반'·'4단계 보조' 항목의 101·104 는 세지 않고 적은 값 — 그 커밋에서 다시 세니 95·98.

### [2026-09-24 19:28] Go의 진화 덱 1부 — 탄생 이전 31장(캡처 10개)
- **기획:** FAQ·2012 발표문(Go at Google)으로 왜 만들었나·첫 두 해·계보·원칙·뺀 것을 쓰고, 원칙은 지금 컴파일러가 지키는지 돌려 봄.
- **TC:** 캡처 10개 — 정상(키워드 25개·합성·오류 값·소수 체·선언 문법) / 경계(쓰지 않는 import·소문자 이름·암묵 수 변환 거절, gofmt -d 종료 1).
- **개발:** `goevo/deck/sections/01_origins.html`, `goevo/ex/01/`(9개), `goevo/exps/p01.py`, `goevo/deck/claims/p01.md`, `goevo/deck/glossary/p01.txt` 외
- **검증:** 1부 조립 오류 0 · 역검증·인용·주장 검사 통과
- **비고:** 문서에 근거가 없는 문장 2개(설계자=Plan 9 사람들, 소수 체의 기원)는 뺐다.

---
## Archive
- [2026-09](history/archive/history-2026-09.md) — 148 entries
