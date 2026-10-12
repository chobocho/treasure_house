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
