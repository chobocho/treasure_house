### [2026-09-24 19:28] Go의 진화 덱 1부 — 탄생 이전 31장(캡처 10개)
- **기획:** FAQ·2012 발표문(Go at Google)으로 왜 만들었나·첫 두 해·계보·원칙·뺀 것을 쓰고, 원칙은 지금 컴파일러가 지키는지 돌려 봄.
- **TC:** 캡처 10개 — 정상(키워드 25개·합성·오류 값·소수 체·선언 문법) / 경계(쓰지 않는 import·소문자 이름·암묵 수 변환 거절, gofmt -d 종료 1).
- **개발:** `goevo/deck/sections/01_origins.html`, `goevo/ex/01/`(9개), `goevo/exps/p01.py`, `goevo/deck/claims/p01.md`, `goevo/deck/glossary/p01.txt` 외
- **검증:** 1부 조립 오류 0 · 역검증·인용·주장 검사 통과
- **비고:** 문서에 근거가 없는 문장 2개(설계자=Plan 9 사람들, 소수 체의 기원)는 뺐다.

### [2026-09-24 19:19] Go의 진화 덱 2부 — 공개에서 Go 1 까지 44장(캡처 22개)
- **기획:** 공개·주간 스냅숏·gofix·Go 1 예고를 문서로, Go 1 의 언어 정리는 더한 것은 실행·없앤 것은 지금 컴파일러의 거절로 보임.
- **TC:** 캡처 20개 + 문서 계산 표 5개 — 정상(append 문자열·rune·delete·같음 등 11개) / 경계(옛 삭제 문법·os.Error·받기 전용 close·가려진 결과·함수 비교·옛 import 6개는 exit 1).
- **개발:** `goevo/deck/sections/02_to_go1.html`, `goevo/data/features/p02.tsv`, `goevo/deck/claims/p02.md`, `goevo/exps/p02.py`, `goevo/ex/02/`(17개), `goevo/data/quotes.tsv`, `goevo/Makefile` 외
- **검증:** 2부 조립 오류 0 · 역검증·인용·상호참조·주장 검사 통과 (3·4부는 작업 중이라 전체 make all 은 다음 커밋에)
- **비고:** 주간 스냅숏 수는 문서 절 89개·태그 99개로 출처마다 달라 둘 다 실음.

### [2026-09-24 19:08] Go의 진화 덱 4단계 보조 — 부 예산 분배·go 잠금·실험 차례
- **기획:** 릴리스마다 기능 장 수를 노트 길이에 비례해 나누고(최신 셋 ×2), go vet 도 실험과 같은 잠금을 잡게 해 서브에이전트 둘이 동시에 일할 수 있게 함.
- **TC:** 3건 — 정상(비례·합계) / 경계(가중치 2배, 끝수 큰 나머지 차례의 결정성).
- **개발:** `goevo/tools/budget_hint.py`, `goevo/tools/tests/test_budget_hint.py`, `goevo/Makefile`, `goevo/run_all.py`, `goevo/exps/ORDER`, `goevo/PLAN.md`
- **검증:** 104 passed, 0 failed
- **비고:** 1.1–1.8 언어 변화는 go 줄로 막히지 않음을 확인(1.9 별칭·1.13 이후만) — 해당 부는 현재 동작 + 문서 배지로 쓴다.

### [2026-09-24 19:03] Go의 진화 덱 0부 — 길잡이 11장(증거 방식 캡처 11개)
- **기획:** 두 심판(설치된 go·공식 문서)과, 옛 툴체인 없이 전·후를 보이는 네 가지 꼴을 진짜 캡처로 설명.
- **TC:** 캡처 11개 — 정상(go 1.22 range 3 → 012, go 1.21 panic(nil) → PanicNilError) / 경계(go 줄 1.21 로 내리면 컴파일 거절, go 줄 1.20·GODEBUG=panicnil=1 → nil, 옛 툴체인 받기 실패, -race 불가).
- **개발:** `goevo/deck/sections/00_start.html`, `goevo/ex/00/`(3개 예제), `goevo/exps/p00.py`, `goevo/exps/ORDER`, `goevo/out/`(캡처 11개) 외
- **검증:** 101 passed, 0 failed · make all SKEL=1 오류 0건 · 24장
- **비고:** 7부는 panic(nil)·정수 range 기초를 되풀이하지 말고 0부로 잇는다.

### [2026-09-24 19:02] Go의 진화 덱 4단계 기반 — gover·run_all·부별 자료 파일
- **기획:** 예제를 결정론 환경에서 go 하나로만(flock) 돌리고 캡처를 정규화. 서브에이전트 둘이 부를 나눠 쓰도록 기능 목록·주장·용어를 부별 파일로.
- **TC:** 28건 — 정상(언어 버전 내리기·GODEBUG 첫 줄·개관 표) / 경계(경로 앞머리 오치환, 벤치 반복수·ns/op, 셸 기호 거절, 이름 겹침, 기대 밖 종료 코드, 108칸 넘는 캡처).
- **개발:** `goevo/tools/gover.py`, `goevo/run_all.py`, `goevo/deck/cites.py`, `goevo/deck/gen_tables.py`, `goevo/deck/build_deck.py`, `goevo/deck/verify_deck.py` 외 15개 파일
- **검증:** 101 passed, 0 failed
- **비고:** 컴파일러 오류 줄(124칸)은 자르지 않고 화면에서만 접는다(term wrap, 200칸 상한).

### [2026-09-24 18:51] Go의 진화 덱 3단계(1) — 생성 표 넷(make_data)
- **기획:** 릴리스·API 증가·GODEBUG·인용 키 표를 docs/ 와 설치된 go 의 소스(godebugs/table.go)에서 만든다. features.tsv 검사(버전·인용 대조)도 여기.
- **TC:** 18건 — 정상(go1·go1.N.0·부 릴리스, 새 패키지, 설정 표) / 경계(플랫폼 꼬리·//deprecated·주석 처리된 설정, 틀린 버전·없는 절·중복 id, 안 쓴 부 대기).
- **개발:** `goevo/tools/make_data.py`, `goevo/tools/tests/test_make_data.py`, `goevo/deck/check_xref.py`, `goevo/data/releases.tsv` 외 10개 파일
- **검증:** 67 passed, 0 failed · make all SKEL=1 오류 0건
- **비고:** 릴리스 289행(큰 릴리스 28), GODEBUG 50행, 인용 키 136개.

### [2026-09-24 18:49] Go의 진화 덱 2단계 — 공식 문서 받기(fetch_docs·html_text)
- **기획:** 릴리스 페이지에서 큰 릴리스 28개를 읽어 노트·API 목록을 받고, 명세·FAQ·godebug·블로그 120편·태그를 docs/ 캐시로. 1.28 초안은 go.dev 가 비어 tip 사이트에서.
- **TC:** 20건 — 정상(제목·dt·문단·pre·명세 머리·마크다운) / 경계(주석·nav·footer 제거, 중첩 li>p, Go 1 표기, 초안 주소, 경로 중복).
- **개발:** `goevo/tools/fetch_docs.py`, `goevo/tools/html_text.py`, `goevo/tools/tests/test_docs_tools.py`, `goevo/docs/FETCHED.txt` 외 8개 파일
- **검증:** 49 passed, 0 failed · make docs 194개 실패 0
- **비고:** 명세·API 는 설치된 go 와 같은 태그 go1.27.1 에 고정.

### [2026-09-24 18:15] Go의 진화 덱 1단계 — 뼈대(make all SKEL=1 초록, 20장)
- **기획:** git/deck 조립기·검사기를 그대로 복사하고 PLAN §1 만큼만 고침. GIT 지시자 대신 GOVER(go.mod 언어 버전·GODEBUG 캡처)·REL(릴리스 날짜) 지시자, 상한 1000장·부 예산 +10% 오류.
- **TC:** 29건 — 정상(GOVER·REL·인용 키·배지) / 경계(1.0↔go1, 1.1↔1.10, 조사 붙은 '1.22에서', HTTP/1.1·1.5배 제외, API 줄 전체 일치). RED 확인 뒤 GREEN.
- **개발:** `goevo/Makefile`, `goevo/deck/build_deck.py`, `goevo/deck/cites.py`, `goevo/deck/check_claims.py`, `goevo/deck/check_xref.py`, `goevo/deck/check_deck.js`, `goevo/deck/base/head.html`, `goevo/tools/tests/test_deck_rules.py` 외 52개 파일
- **검증:** 29 passed, 0 failed · make all SKEL=1 오류 0건·경고 0
- **비고:** 표지 버전 13개·날짜 1개는 go.dev 릴리스 페이지로 확인해 claims.md 에 기록. 다음은 2단계(fetch_docs·html_text).

### [2026-09-24 18:01] Go의 진화 덱 지시서 — §9 결정 12건 확정 기록
- **기획:** 사용자가 §9 권고안 12건을 그대로 확정. 지시서 진행 로그와 메모리에 "재질문 금지"로 기록.
- **TC:** 해당 없음(문서만).
- **개발:** `goevo/PLAN.md`
- **검증:** 진행 로그 항목 추가만, 기존 항목 불변.
- **비고:** 다음은 Opus 가 1단계(뼈대, `make all SKEL=1`)부터 시작.

### [2026-09-24 17:58] Go의 진화 덱 작업 지시서 작성 (goevo/PLAN.md)
- **기획:** git/deck 조립기 계보로 Go 역사·버전별 개선점 덱을 만들기 위한 Opus 용 영문 지시서. 상한 1000장, 목표 820–960, 12부 예산 합계 962.
- **TC:** 해당 없음(문서만). 기계 사실은 실측 — go 1.27.1 만 있고 옛 툴체인 내려받기 불가, go.mod 언어 지시자로 전/후 재현 가능, 공식 문서·API 파일 접속 확인.
- **개발:** `goevo/PLAN.md`
- **검증:** UTF-8·모지바케 없음, 부별 예산 합계 962 ≤ 1000 확인
- **비고:** §9 결정 12건 사용자 확인 대기. 코드·자료·docs 는 아직 없음.

### [2026-09-24 17:25] 옛 계열 덱 28종 ←→ 먹통 수정 — 입력칸·버튼 포커스가 방향키·Space 를 가로채던 버그, 엔진 가드 4형 통일
- **기획:** 템플릿 계열이 아닌 옛 엔진 28종. 가드가 sel 만(15)·+INPUT(7)·+INPUT/SELECT/TEXTAREA(4)·+CANVAS 2줄(2)로 갈려 있어 정규식 패처로 typing() 으로 통일, CANVAS 예외와 lua_tetris 의 캔버스 포커스 줄은 보존.
- **TC:** DOM 스텁 9건을 28개에 적용 — 수정 전 전부 실패(sel 만: 5건, INPUT 가드: 3건), 수정 후 전부 통과. 스텁은 옛 엔진의 id·cloneNode·remove·canvas 까지 흉내내도록 보강.
- **개발:** `GWBASIC_in_C.html`, `Linux_명령어_핸드북.html`, `체스_전술집.html`, `lua_tetris.html`, `wolfenstein3d-porting-guide.html`, `jq 가이드.html`, `Go_심화_슬라이드.html`, `쿠키_쉽게_배우기.html` 외 20개 파일
- **검증:** 엔진 스텁 28×9 passed, 0 failed · 엔진 구문 검사 28 OK · embed_mono --check 28 통과 · diff 모양 균일(+16/-1, 2줄 가드 2종만 +16/-2)
- **비고:** 이로써 `e.target === sel` 가드를 가진 덱 전부(템플릿 계열 35 + 옛 계열 28)에 같은 수정이 들어갔다.

### [2026-09-24 17:14] 템플릿 파생 덱 24종 ←→ 먹통 수정 — 입력칸·버튼 포커스가 방향키·Space 를 가로채던 버그, 빌더 뼈대 8개 동기
- **기획:** 템플릿에서 고친 엔진 결함을 파생 덱 24종에 이식. 빌드로 생성되는 8종은 `*/deck/base/tail.html` 도 같이 고쳐 재빌드 시 되돌아가지 않게 함.
- **TC:** 템플릿과 같은 DOM 스텁 9건을 24개 덱에 적용 — 수정 전 24개 모두 실패(Node.js 3건, 나머지 5건), 수정 후 전부 통과.
- **개발:** `C_기초.html`, `Go_기초.html`, `Lua_기초.html`, `TypeScript_기초.html`, `Node.js_완전_가이드.html`, `Git_대백과사전.html`, `압축_대백과사전.html`, `git/deck/base/tail.html` 외 24개 파일
- **검증:** 엔진 스텁 24×9 passed, 0 failed · 엔진 구문 검사 24 OK · embed_mono --check 24 통과 · 뼈대 8개와 완성 덱의 엔진 일치
- **비고:** Node.js 덱은 자체 INPUT 가드가 체크박스까지 막던 것을 typing() 으로 교체. scratch 의 wifi·db tail.html 도 같이 고쳤으나 gitignore 라 미커밋.

### [2026-09-24 17:05] 파이썬의 진화 덱 ←→ 먹통 수정 — 입력칸·버튼 포커스가 방향키·Space 를 가로채던 버그 1건
- **기획:** 엔진이 템플릿과 동일해 같은 결함을 갖고 있었다. 템플릿과 같은 typing()·Space 양보·떠나는 장 blur 이식.
- **TC:** 템플릿과 같은 DOM 스텁 9건 — 정상: 본문·버튼·체크박스에서 ←→. 경계: 입력칸 ←·t, 버튼·체크박스 Space, 장 이동 뒤 포커스 잔류.
- **개발:** `파이썬의_진화.html`
- **검증:** 엔진 스텁 9 passed, 0 failed · 태그 균형·중복 id 0 · embed_mono --check 통과

### [2026-09-24 17:05] 슬라이드 덱 템플릿 리뷰 — ←→ 먹통 수정 1건·문서 불일치 4건·공용 셸 안내 2곳
- **기획:** 9/21 덱 17개에 적용된 ←→ 먹통 수정이 템플릿에 빠져 있었다. 엔진 keydown 에 typing() 판별·Space 양보·떠나는 장 blur 를 웹 인증 덱과 같은 코드로 이식.
- **TC:** DOM 스텁(node)으로 엔진만 적재해 9건 — 정상: 본문·버튼·체크박스에서 ←→. 경계: 숫자 입력칸 ←, 글 입력칸 t, 버튼·체크박스 Space, 장 이동 뒤 포커스 잔류.
- **개발:** `template.html`
- **검증:** 엔진 스텁 9 passed, 0 failed · 하이라이터 11개 언어 샘플 정상 · 태그 균형·중복 id 0 · embed_mono --check 통과
- **비고:** 문서 정정: :root 색 12→15개, head 주석 "3줄", 지원 언어 표에 bas·make·xml·별칭, .term 주석. 인쇄 모드의 미방문 장 하이라이팅은 미처리.

### [2026-09-23 07:52] 파이썬의 진화 덱 3.15 부 리뷰 — 사실오류 6건·근거 보강 4건·표기 4건 정정
- **기획:** 9부 56장 통독 + PEP 690·810·416·661, 3.15 공식 문서(cmdline·configure·profiling.sampling)와 대조.
- **TC:** 정상: 9부 py 블록 33개 재실행. 경계: importtime·Tachyon 출력 재측정, 8부와 중복 서술(calendar) 교차 확인.
- **개발:** `파이썬의_진화.html`
- **검증:** 31개 정상 종료 + 의도된 예외 2개 · id 중복 0 · 357장 · embed_mono --check 통과
- **비고:** 미실행 출력(importtime)을 실제 값으로 교체. 가로 폭 렌더링은 Playwright 불가로 미확인.

### [2026-09-23 07:22] 파이썬의 진화 덱 — Python 3.15 부(9부) 56장 추가
- **기획:** 3.15.0rc2 whatsnew 기준으로 새 9부(lazy import·컴프리헨션 풀기·frozendict·sentinel·UTF-8 기본·Tachyon 등 9장) 추가, 총정리를 10부로.
- **TC:** 정상: 9부 py 블록 33개 3.15rc2 실행·출력 대조. 경계: lazy 금지 위치 SyntaxError·필터 모드·3.14 호환 동작 확인.
- **개발:** `파이썬의_진화.html`, `index.html`, `README.md`
- **검증:** 33개 중 31개 통과(나머지 2개는 의도된 예외·단독 실행 불가 모듈) · id 중복 0 · embed_mono --check 통과
- **비고:** `-X lazy_imports=none`은 실존하지 않아 뺐음. 정식판(10-01) 뒤 성능 수치 재확인 필요.

### [2026-09-21 06:54] 도스 쿼터뷰 RPG 덱 — ←→ 먹통 수정(체크박스 포커스)
- **기획:** 엔진이 모든 INPUT 포커스면 ←→를 무시해, 체크박스 12개를 누르면 이후 물리 키보드로 못 넘김.
- **TC:** 정상: 체크박스·데모 버튼·내비 버튼 포커스에서 ←→ 이동. 경계: 텍스트·range·textarea 는 안 넘김, 체크박스 위 스페이스 양보.
- **개발:** `isorpg/deck/base/tail.html`, `도스_쿼터뷰_RPG_수학_해부.html`
- **검증:** DOM 스텁 9항목 전부 통과(수정 전 실패 있음) · embed_mono --check 통과

### [2026-09-21 06:54] 도스 RTS 덱 — ←→ 먹통 수정(체크박스 포커스)
- **기획:** 엔진이 모든 INPUT 포커스면 ←→를 무시해, 체크박스 12개를 누르면 이후 물리 키보드로 못 넘김.
- **TC:** 정상: 체크박스·데모 버튼·내비 버튼 포커스에서 ←→ 이동. 경계: 텍스트·range·textarea 는 안 넘김, 체크박스 위 스페이스 양보.
- **개발:** `rts/deck/base/tail.html`, `도스_RTS_전략게임_수학_해부.html`
- **검증:** DOM 스텁 9항목 전부 통과(수정 전 실패 있음) · embed_mono --check 통과

### [2026-09-21 06:54] 복셀 엔진 덱 — ←→ 먹통 수정(버튼 포커스)
- **기획:** 엔진이 INPUT·BUTTON 포커스면 ←→를 무시해, 데모 버튼를 누르면 이후 물리 키보드로 못 넘김.
- **TC:** 정상: 체크박스·데모 버튼·내비 버튼 포커스에서 ←→ 이동. 경계: 텍스트·range·textarea 는 안 넘김, 체크박스 위 스페이스 양보.
- **개발:** `복셀_엔진_만들기.html`
- **검증:** DOM 스텁 9항목 전부 통과(수정 전 실패 있음) · embed_mono --check 통과

### [2026-09-21 06:54] 러브2D 아웃런 덱 — ←→ 먹통 수정(버튼 포커스)
- **기획:** 엔진이 INPUT·BUTTON 포커스면 ←→를 무시해, 데모 버튼를 누르면 이후 물리 키보드로 못 넘김.
- **TC:** 정상: 체크박스·데모 버튼·내비 버튼 포커스에서 ←→ 이동. 경계: 텍스트·range·textarea 는 안 넘김, 체크박스 위 스페이스 양보.
- **개발:** `러브2D_아웃런_레이싱_게임.html`
- **검증:** DOM 스텁 9항목 전부 통과(수정 전 실패 있음) · embed_mono --check 통과

### [2026-09-21 06:54] 슈퍼패미콤 덱 — ←→ 먹통 수정(버튼 포커스)
- **기획:** 엔진이 INPUT·BUTTON 포커스면 ←→를 무시해, 화면 ‹ › 버튼를 누르면 이후 물리 키보드로 못 넘김.
- **TC:** 정상: 체크박스·데모 버튼·내비 버튼 포커스에서 ←→ 이동. 경계: 텍스트·range·textarea 는 안 넘김, 체크박스 위 스페이스 양보.
- **개발:** `슈퍼패미콤_비디오모드.html`
- **검증:** DOM 스텁 9항목 전부 통과(수정 전 실패 있음) · embed_mono --check 통과

### [2026-09-21 06:54] Penpot·ArgoCD 덱 — ←→ 먹통 수정(버튼 포커스)
- **기획:** 엔진이 INPUT·BUTTON 포커스면 ←→를 무시해, 화면 ‹ › 버튼를 누르면 이후 물리 키보드로 못 넘김.
- **TC:** 정상: 체크박스·데모 버튼·내비 버튼 포커스에서 ←→ 이동. 경계: 텍스트·range·textarea 는 안 넘김, 체크박스 위 스페이스 양보.
- **개발:** `Penpot_ArgoCD_배포_가이드.html`
- **검증:** DOM 스텁 9항목 전부 통과(수정 전 실패 있음) · embed_mono --check 통과

### [2026-09-21 06:54] 도스박스 덱 — ←→ 먹통 수정(체크박스·버튼 포커스)
- **기획:** 엔진이 내비 버튼 밖의 INPUT·BUTTON 포커스면 ←→를 무시해, 데모 버튼·체크박스를 누르면 이후 물리 키보드로 못 넘김.
- **TC:** 정상: 체크박스·데모 버튼·내비 버튼 포커스에서 ←→ 이동. 경계: 텍스트·range·textarea 는 안 넘김, 체크박스 위 스페이스 양보.
- **개발:** `도스박스_해부.html`
- **검증:** DOM 스텁 9항목 전부 통과(수정 전 실패 있음) · embed_mono --check 통과

---
## Archive
- [2026-09](history/archive/history-2026-09.md) — 126 entries
