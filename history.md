### [2026-10-12 15:08] Rust 덱 21부 매크로·unsafe·FFI 심화 뒤 절반 — 38장, 부 전체 79장
- **기획:** 3장은 2장의 도구만으로 `MyVec<T>` 를 단계별로 만들고 표준 `Vec` 과 견준다. 4장은 2024 에디션 표기로 C 함수 부르기·`CString`·콜백·`#[repr(C)]`·내보내기·`union`·`static mut`. 정의되지 않은 동작 검사기가 없음을 다시 밝힌다.
- **TC:** 정상(같은 연산 대본을 `MyVec` 과 `Vec` 에 돌려 같은 결과, 값 13개가 네 경로에서 한 번씩 정리) / 경계(크기 0 인 타입 E0080, 너무 큰 용량 패닉, 범위 밖 인덱스, 먹다 만 반복자, 안쪽 NUL, 없는 환경 변수, 2021 과 2024 쌍둥이).
- **개발:** `rust/deck/sections/21b_low.html`, `rust/deck/sections/21_low.html`, `rust/ex/21/**`, `rust/out/21/**`, `rust/data/features.tsv`, `rust/deck/order.txt`, `index.html`, `README.md` 외 3개 파일
- **검증:** make all 1,349장 오류 0건·알림 0건·어긋남 0건 · 21부 예제 80개 재실행 3회 모두 일치 · 버전 표기 112건 대조 오류 0건
- **비고:** 리뷰 전. `Index` 대신 `Deref` 로 인덱싱을 얻었다(목차와 다름). `vec_*.rs` 는 조각에서 조립한 쌍둥이.

### [2026-10-12 14:23] Rust 덱 21부 매크로·unsafe·FFI 심화 앞 절반 — 41장, 예제 45개
- **기획:** 16부의 둘째 층. 1장은 `macro_rules!` 의 종류 지정자·중첩 반복·재귀·`$crate`, 2장은 날 포인터와 `alloc`·`MaybeUninit`·`transmute`. 화면은 정의되지 않은 동작이 없음을 보여 주지 못한다고 밝히고, 그런 프로그램은 돌리지 않는다.
- **TC:** 정상(종류 지정자별 쌍둥이, 두 크레이트로 본 `#[macro_export]`, 한 번씩만 정리되는 값) / 경계(코드 없는 매크로 오류, 재귀 한도, 빈 슬라이스의 끝 포인터, 크기가 다른 `transmute` E0512, 채우다 만 배열).
- **개발:** `rust/deck/sections/21_low.html`, `rust/ex/21/**`, `rust/out/21/**`, `rust/data/features.tsv`, `rust/deck/order.txt`, `rust/deck/sections/00_start.html`, `index.html`, `README.md` 외 3개 파일
- **검증:** make all 1,311장 오류 0건·어긋남 0건 · 21부 예제 45개 재실행 3회 모두 일치 · 버전 표기 106건 대조 오류 0건
- **비고:** 리뷰 전. 뒤 절반(3장 작은 Vec, 4장 FFI)은 다음 커밋. 표준 문서 인용은 이 툴체인의 문서가 아니라 웹 문서와 대조했다.

### [2026-10-12 13:33] Rust 덱 20부 동시성 심화 리뷰 — 결함 21건·흐름 5건 정정
- **기획:** 20부 69장과 예제 51개를 처음 읽는 리뷰어 하나가 정독. 화면이 스레드 순서에 기대지 않는지, 추론으로 적은 문장, 두 번에 나눠 쓴 앞뒤 절반의 이음매를 중점으로 봤다.
- **TC:** 정상(예제 51개 재실행 3회 일치, 쌍둥이 diff, 인용 범위와 줄 번호 대조) / 경계(`map_or` 의 Err 갈래를 손으로 만든 값으로 지나기, 원소보다 많은 스레드 수, 빈 슬라이스, 받는 쪽이 사라진 `sync_channel`).
- **개발:** `rust/deck/sections/20_conc.html`, `rust/deck/sections/20b_conc.html`, `rust/ex/20/send_error.rs`, `rust/ex/20/split_auto.rs`, `rust/ex/20/tl_basic.rs`, `rust/out/20/split_auto.txt`, `rust/deck/AUTHORING.md`, `rust/PLAN.md` 외 2개 파일
- **검증:** make all 1,270장 오류 0건·어긋남 0건 · 20부 예제 51개 재실행 3회 모두 일치
- **비고:** 근거없음 8·순서 4·표기 4·증거불일치 2·코드 2·퀴즈 1. 장수 변동 없음. `Job` 의 `+ 'static` 표기 차이와 표준 문서 인용 대조는 남은 일.

### [2026-10-12 09:20] Rust 덱 19부 제네릭·트레이트 심화 — 96장, 예제 119개
- **기획:** 10부의 둘째 층. 바운드 더 깊이, 연관 타입과 GATs, 트레이트 객체 심화, 타입으로 설계하기, 고차 바운드와 함수, const 와 제네릭. 슬라이드마다 컴파일되지 않거나 불편한 프로그램에서 시작한다.
- **TC:** 정상(조건부 구현, 빌려주는 반복자, 타입 상태 빌더, 차원이 맞는 행렬 곱) / 경계(겹치는 구현 E0119, 쓰이지 않는 타입 인자 E0392, 상수 넘침 E0080, 길이 0 인 인스턴스에서만 나는 const 단언, 봉인한 트레이트를 바깥 크레이트에서 구현).
- **개발:** `rust/deck/sections/19_gen.html`, `rust/deck/sections/19b_gen.html`, `rust/ex/19/**`, `rust/out/19/**`, `rust/data/features.tsv`, `rust/deck/sections/00_start.html`, `rust/deck/sections/01_history.html`, `index.html` 외 `README.md`·`Rust_기초_문법집.html`
- **검증:** make deck 1,196장 오류 0건·알림 0건 · 19부 예제 119개 재실행 5회 모두 일치 · 버전 표기 84건 대조 오류 0건
- **비고:** 리뷰 전. 오류 번호 56종(E0119·E0271·E0107·E0392·E0631·E0080 추가). 예제의 절반 가까이가 실제 컴파일 오류다.

### [2026-10-12 07:26] Rust 덱 18부 표준 라이브러리 둘러보기 — 84장, 예제 66개
- **기획:** 수 더 깊이, 비교와 정렬, 해시와 맵 더, 시간, 프로세스와 환경, 그 밖의 도구 여섯 장. 메서드 목록이 되지 않게 슬라이드마다 작은 문제에서 시작하고 장마다 "하려는 일 → 쓸 것" 표로 닫는다.
- **TC:** 정상(비트·정렬·맵 도구의 출력, 자식 프로세스의 종료 상태와 출력 받기) / 경계(상수 밀기 넘침의 컴파일 오류, NaN 에서 패닉하는 partial_cmp, Eq 와 Hash 가 어긋난 키, 음수가 될 Duration, 없는 프로그램·환경 변수).
- **개발:** `rust/deck/sections/18_std.html`, `rust/deck/sections/18b_std.html`, `rust/ex/18/**`, `rust/out/18/**`, `rust/data/features.tsv`, `rust/deck/sections/00_start.html`, `index.html`, `README.md`, `Rust_기초_문법집.html`
- **검증:** make deck 1,099장 오류 0건·알림 0건 · 18부 예제 66개 재실행 7회 모두 일치 · 버전 표기 79건 대조 오류 0건
- **비고:** 리뷰 전. 시간 예제는 걸린 값을 찍지 않고 반드시 참인 비교만 찍는다. 환경 변수는 예제가 정한 것만 찍는다.

### [2026-10-12 06:23] Rust 덱 지도·카드를 17부까지 반영 — 1,015장
- **기획:** 17부가 들어간 채로 공개하기 전에, 0부의 책 지도와 16부의 맺음말, 카드·README 의 수치를 실제 덱에 맞춘다.
- **TC:** 정상(지도의 17 이 17부 표지로 간다) / 경계(카드의 장수·예제·캡처·퀴즈·버전 표기 수를 조립 결과에서 다시 센 값과 대조).
- **개발:** `rust/deck/sections/00_start.html`, `rust/deck/sections/16_more.html`, `index.html`, `README.md`, `Rust_기초_문법집.html`
- **검증:** make deck 1,015장 오류 0건·알림 0건
- **비고:** 예제 684·캡처 705·퀴즈 80·오류 번호 50종·버전 표기 41건·용어집 64낱말. 새 부가 들어올 때마다 지도와 카드를 같은 커밋에서 고친다.

### [2026-10-12 05:43] Rust 덱 17부 입출력과 파일 — 93장, 예제 62개
- **기획:** 확장의 첫 부. 표준 출력·오류 출력, 표준 입력, 파일 읽기·쓰기, 경로와 디렉터리, 작은 도구(cat·wc·head) 여섯 장. 9부의 Result·? 위에 얹고 다시 가르치지 않는다.
- **TC:** 정상(리다이렉트로 가른 두 흐름, 예제가 싣고 온 파일 읽기, BufWriter 가 flush 전후에 파일에 쓴 바이트 수) / 경계(없는 파일·디렉터리·UTF-8 아닌 바이트와 이름, 끊긴 파이프, 실패하는 flush, 입력의 끝, 틀린 인자와 종료 코드 0·1·2).
- **개발:** `rust/deck/sections/17_io.html`, `rust/deck/sections/17b_io.html`, `rust/ex/17/**`, `rust/out/17/**`, `rust/deck/order.txt`, `rust/PLAN.md`, `Rust_기초_문법집.html`
- **검증:** make deck 1,015장 오류 0건·알림 0건 · 17부 예제 62개 재실행 5회 모두 일치
- **비고:** 리뷰 전. 버전 배지 7건은 근거 표에 행을 더한 뒤 붙인다. 카드·README 수치는 확장이 끝날 때 한 번에 고친다.

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

---
## Archive
- [2026-09](history/archive/history-2026-09.md) — 159 entries
