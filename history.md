### [2026-09-18 23:07] Git 덱 전수 리뷰 2차 — 퀴즈·그림·표, 17부 전체, 19부 해설
- **기획:** 1차에서 덜 본 곳(퀴즈 정답, 그림, 명령어 사전 161장)을 서브에이전트 둘과 기계 대조로.
- **TC:** -s ours revert·설정 없는 pull·bisect 예를 진짜 git 으로 재현, 산문 속 해시 52개 대조.
- **개발:** `git/deck/sections/`(8개), `git/deck/gen_cmdref.py`(신규), `git/deck/gen_figs.py`, `git/exps/cmdref.py` 외
- **검증:** record.sh --check(빈 디렉터리) 1,240개 3회 동일 · make all SKEL=1 오류 0건
- **비고:** mygit merge-base 의 같은 날짜 차례가 git 과 다름(Python·Java 는 실행마다) — git 식으로 고칠 계획.

### [2026-09-18 18:15] Git 덱 재현 검사 강화 — 재실행마다 실험 디렉터리를 비운다
- **기획:** 저장소 밖(../)에 남은 것 때문에 첫 실행만 다른 캡처는 세 번 검사로 안 잡힌다.
- **TC:** scratch/repos 를 비운 채 전체 실행 → 캡처 1건(pre-push 훅) 차이 발견.
- **개발:** `git/tools/record.sh`, `git/exps/config_hooks.py`, `git/exps/merge2.py`, `git/out/`
- **검증:** 새 record.sh --check 로 1,240개 3회 동일 · make all SKEL=1 오류 0건

### [2026-09-18 16:48] Git 덱 전수 리뷰 1차 — 51건 중 49건 정정
- **기획:** 서브에이전트 둘이 0~10부·11~20부를 원문·캡처·진짜 git 과 대조, 지적마다 다시 확인.
- **TC:** really-refresh·로컬 clone·worktree 는 진짜 git 으로 재현해 확인.
- **개발:** `git/deck/sections/`(17개), `git/deck/glossary.txt`, `git/data/events.tsv`, `git/exps/tools2.py` 외
- **검증:** make all SKEL=1 오류 0건 · 데모 20건 통과
- **비고:** 용어집 링크 60여 곳 재지정. 명령어 사전의 "돌린 곳" 누락은 다음 리뷰로.

### [2026-09-18 16:24] Git 대백과사전 공개 — index·README 에 새 절 "🌿 Git & 버전 관리"
- **기획:** PLAN 결정 1 대로 "🎬 자동화 & CI/CD" 앞에 새 절, 카드의 수는 빌드 출력에서 센 실제 값.
- **TC:** 폰트 검사 통과 · make all SKEL=1 오류 0건.
- **개발:** `index.html`, `README.md`
- **검증:** 1,819장 · 캡처 1,240개 · 데모 9 · 퀴즈 61 · 용어 255
- **비고:** 다음은 14단계 전수 리뷰(서브에이전트 둘). push 는 하지 않았다.

### [2026-09-18 16:23] Git 덱 11단계 — 데모 9개, 기댓값 20건은 진짜 git·golden 에서
- **기획:** 데모 정답을 데모 스스로 내지 않게 golden 과 새 실험 demos 의 캡처에서 옮긴다.
- **TC:** SHA-1 벡터 73·diff agree 29쌍·merge 장면 9개를 node 로 golden 과 대조, CASES 20건.
- **개발:** `git/deck/demos.js`, `git/deck/check_deck.js`, `git/exps/demos.py`, `git/exps/dag.py`, 섹션 6개
- **검증:** check_deck 데모 9개 배선·20건 통과 · make all SKEL=1 오류 0건

### [2026-09-18 16:16] Git 덱 9단계 — 본문 0~20부 1,810장, 소스 커버리지 100%
- **기획:** 부마다 실험으로 주장을 받치고 한 부 한 커밋. 19부는 다섯 언어 소스 전문(사용자 결정).
- **TC:** 새 실험 14종(history·appendix 포함), record.sh --check 여섯 번 통과(마지막 1,232개).
- **개발:** `git/deck/sections/`(21개), `git/exps/`, `git/deck/glossary.txt`, `git/data/`, `git/PLAN.md` 외 다수
- **검증:** 캡처 1,232개 3회 동일 · 커버리지 21,820/21,820줄 · 근거 없는 날짜 0건
- **비고:** 16부 장면 4개·17부 명령 2개·19부 범위 표 등 오류를 실험으로 찾아 정정. 커밋 7371668…7b70193.

### [2026-09-18 09:56] Git 덱 8단계 — 도해 17장(캡처·golden·자료에서 읽어 그림)
- **기획:** 그림 속 이름·크기·날짜를 손으로 적지 않는다. 캡처가 가정과 어긋나면 그리지 않고 멈춘다.
- **TC:** make figs-check 어긋남 0 · PNG 17장 눈 검사로 13곳 정정 · 바꾼 실험 셋 두 번 돌려 md5 동일.
- **개발:** `git/deck/gen_figs.py`, `git/deck/svgkit.py`, `git/deck/figs/`(17개), `git/exps/hello.py`·`dag.py`·`pack.py`, `git/out/`, `git/PLAN.md`
- **검증:** make all SKEL=1 오류 0건 · 캡처 702개 108칸 초과 0
- **비고:** 이 기계 find(bfs)가 proot 에서 객체 파일을 못 봐 캡처 3개가 비어 있던 것을 고침. 다음은 9단계 본문.

### [2026-09-18 08:38] Git 덱 7단계 — run_all.py 실험 16종·캡처 695개·세 번 재현
- **기획:** 덱의 모든 출력은 진짜 git(또는 mygit)이 만든다. 실험 16종을 한 번에 돌리고 세 번 같은지 본다.
- **TC:** mygit 대본 23줄을 5개 언어로 돌려 Python·진짜 git 과 대조, 명령어 사전 -h 151개·실행 예 74개.
- **개발:** `git/run_all.py`, `git/exps/`(16개), `git/out/`, `git/deck/budget.txt`, `git/deck/pending.txt`, `git/PLAN.md`
- **검증:** record.sh --check 3회 695개 동일 · 108칸 초과 0 · 대조표 60칸 ok · make all SKEL=1 통과
- **비고:** 한 번 ≈ 8분. 파일 수 실험은 계획의 10만이 아니라 2만까지. 다음은 8단계 도해.

### [2026-09-18 07:19] Termux 덱 전수 리뷰 4차 — 사실오류 7건·퀴즈 4건·근거없음 3건·캡처불일치 2건·교차참조 2건·한국어 2건 정정
- **기획:** 9~16부를 두 번째로 독립 정독. 이로써 덱의 두 절반이 모두 독립 정독을 두 번씩 받음.
- **TC:** 지적 20건을 핀 소스(port_switch.c·pkg.in)·보안 정책·공개 글·캡처로 재검증.
- **개발:** `termux/deck/sections/09~16_*.html`, `termux/deck/claims.md`, `termux/PLAN.md`, `Termux_대백과사전.html`
- **검증:** make all 오류 0건 · 역검증 통과 · 인용 범위·상호참조 어긋남 0건
- **비고:** 리뷰 누계 26·23·37·20건. 네이티브 값은 여전히 대기.

### [2026-09-18 06:58] Git 덱 6단계 — mygit 을 Go·TypeScript·Java·C++ 로(각 12단계)
- **기획:** SPEC 하나로 네 언어를 더 짓는다. Go·C++ 는 직접, TS·Java 는 서브에이전트 하나씩. 단계마다 한 커밋.
- **TC:** 언어마다 Python 시험을 그대로 옮기고 장면 21개를 다시 돌림(첫 커밋 전 merge·한쪽만 지운 경로 장면 추가).
- **개발:** `git/go/`, `git/ts/`, `git/java/`, `git/cpp/`(손으로 짠 inflate), `git/py/mygit/merge.py`·`cli.py`, `git/SPEC.md`, `git/Makefile`, `git/PLAN.md`
- **검증:** go ok · ts 134/135(1 skip) · java 134/135(1 skip) · cpp 13개 0 실패 · 장면 21개 전부
- **비고:** 소스 합계 ≈ 21,000줄 — 부록 A 전문을 다 실으면 470장 남짓. 10단계에서 Python 전문 + 발췌로 정할 것.

### [2026-09-18 06:23] Termux 덱 전수 리뷰 3차 — 네이티브 8건·교차참조 15건·캡처불일치 7건·초보자 3건·한국어 3건·모순 1건 정정
- **기획:** 0~8부와 부록을 2차의 각도(교차참조·산문과 캡처·흐름)로 다시 읽음. 없는 네이티브 캡처를 있는 듯 말한 문장을 모두 바로잡음.
- **TC:** 지적 37건을 캡처·스크립트 줄·다른 부의 grep 으로 재검증. 도구 오류가 든 캡처는 0건.
- **개발:** `termux/deck/sections/00~08·17_*.html`, `termux/PLAN.md`, `Termux_대백과사전.html`
- **검증:** make all 오류 0건 · 역검증 통과 · 상호참조 어긋남 0건
- **비고:** '장'은 챕터, 슬라이드는 '슬라이드'로 통일. 네이티브 값이 오면 해당 자리를 채울 것.

### [2026-09-18 06:13] Termux 덱 전수 리뷰 2차 — 사실오류 6건·캡처불일치 5건·교차참조 10건·한국어 1건·데모문구 1건 정정
- **기획:** 9~16부와 데모 장을 흐름·산문과 캡처·교차참조·한국어 각도로 다시 읽음. 실패한 채 실린 캡처 1건이 나와 재발 방지 검사를 더함.
- **TC:** run_all.check 시험 1건 먼저(RED 확인): srcpin 경로 오류·파이썬 예외가 든 캡처를 거부한다.
- **개발:** `termux/run_all.py`, `termux/tools/tests/test_run_all.py`, `termux/out/src_security.txt`, `termux/deck/sections/06·08~16_*.html`, `termux/PLAN.md`, `Termux_대백과사전.html`
- **검증:** test_run_all 통과 · 캡처 검사 0건 · make all 오류 0건 · 데모 12건
- **비고:** 2차 지적이 20건을 넘어 계획대로 3차 리뷰를 한다.

### [2026-09-18 06:02] Termux 덱 전수 리뷰 1차 — 사실오류 4건·캡처불일치 2건·인용범위 5건·교차참조 11건·표기 4건 정정
- **기획:** 0~8부는 보조 에이전트가 정독, 9~16부는 숫자를 캡처와 대조. 지적마다 핀 소스·캡처·문서로 다시 확인한 뒤 고침.
- **TC:** 리뷰 26건 재검증(셸 후보 5개·RUN_COMMAND 런타임 권한·Tasker 선택 설정·실행 환경 문서 절 번호 등).
- **개발:** `termux/deck/sections/02~07_*.html`, `termux/deck/claims.md`, `termux/PLAN.md`, `Termux_대백과사전.html`
- **검증:** make all 오류 0건 · 인용 범위 60개 어긋남 0건 · 상호참조 어긋남 0건
- **비고:** apt 가 root 를 막는 까닭은 위키에 있어 미확인 표시를 걷었다. 다음은 리뷰 2차.

### [2026-09-18 05:50] Termux 대백과사전 공개 — index 카드·README(587장)
- **기획:** 뼈대 모드를 끄고 전체 검사를 통과시킨 뒤 공개. 네이티브 값이 없다는 사실을 자리표시 대신 본문에 그대로 적는다.
- **TC:** make all(뼈대 모드 없이) 오류 0건, make record 로 고정 캡처 40개 3회 동일, 글꼴 검사 통과.
- **개발:** `index.html`, `README.md`, `termux/deck/sections/00_start.html`, `03_android.html`, `07_api.html`, `termux/PLAN.md`, `Termux_대백과사전.html`
- **검증:** make all 오류 0건 · stable 40/40 재현 · 587장
- **비고:** data/device.txt(네이티브 값) 미도착 — 오면 native_device 캡처로 채운다. 다음은 리뷰 1·2차.

### [2026-09-18 05:36] Termux 덱 — 데모 3개(경로 번역기·pkg 해석기·팬텀 계산기)
- **기획:** 같은 장의 소스 발췌 규칙을 그대로 옮긴 손으로 만져 보는 데모. 기댓값은 발췌와 캡처에서.
- **TC:** check_deck.js CASES 12건 먼저 — /usr/bin·/system/bin·/bin·상대 경로, in·info·update·upgrade·rm·모르는 명령, 16·40개.
- **개발:** `termux/deck/demos.js`, `termux/deck/check_deck.js`, `termux/deck/sections/05_filesystem.html`, `06_packages.html`, `08_limits.html`, `termux/PLAN.md`
- **검증:** 데모 3개 배선·예외 없음·동작 12건 일치 · make all SKEL=1 오류 0건
- **비고:** 계획의 나머지 7개 데모는 이미 표·캡처가 같은 내용을 보여 빼고 PLAN 에 기록.

### [2026-09-18 05:33] Termux 대백과사전 덱 16·17부 — 마무리·부록(173장)
- **기획:** 지도·오해 12가지·종합 퀴즈, 그리고 용어집 262개·생성 표·소스 전문·퀴즈 색인. 우리 코드 커버리지 100%.
- **TC:** 등급 검사 시험 3건 먼저: 전문 장은 캡처 없이 a, 본문 코드만 장은 여전히 실패, src- 인데 코드 없으면 실패.
- **개발:** `termux/deck/build_deck.py`, `termux/deck/tests/test_tier.py`, `termux/deck/gen_glossary.py`, `termux/deck/glossary.txt`, `termux/deck/sections/16_wrapup.html`, `termux/deck/sections/17_appendix.html` 외 3개 파일
- **검증:** deck 시험 통과 · make all SKEL=1 오류 0건 · 커버리지 3206/3206줄 · 584장
- **비고:** 합계 584장으로 목표 띠보다 적다 — 채우려고 늘리지 않았다(budget.txt 원칙).

### [2026-09-18 05:26] Termux 대백과사전 덱 13부 — AI 에이전트와 이 저장소(8장)
- **기획:** 이 덱을 만든 작업장 자체를 증거로: 메모리, 프로세스, 두 세계의 도구, 규칙 파일, upstream 의 CLAUDE.md.
- **TC:** 캡처 2종(repo_self 스냅샷·src_pd_claude) 추가·session_self 재촬영, 추측 문장 2건 삭제, 조립 검사 오류 0건.
- **개발:** `termux/deck/sections/13_ai_agents.html`, `termux/run_all.py`, `termux/out/` 3개, `termux/deck/claims.md`, `termux/PLAN.md`, `Termux_대백과사전.html`
- **검증:** test_run_all 통과 · make all SKEL=1 오류 0건

### [2026-09-18 05:24] Termux 대백과사전 덱 2부 — 역사(13장)
- **기획:** 2015 시작부터 2026-09 까지를 시대별 연표로. 날짜는 모두 기계로 모은 timeline.tsv 에서 표로 생성.
- **TC:** gen_tables 거르개가 값 여러 개를 받게 시험 5건 먼저(RED 확인) — 값 하나·튜플·빈 튜플·거르개 없음·전체 표.
- **개발:** `termux/deck/gen_tables.py`, `termux/deck/tests/test_gen_tables.py`, `termux/out/tbl_timeline_*.html`, `termux/deck/sections/02_history.html`, `termux/PLAN.md`, `Termux_대백과사전.html`
- **검증:** deck 시험 통과 · make all SKEL=1 오류 0건 · 연도 인용 27건 근거 있음

### [2026-09-18 05:21] Termux 대백과사전 덱 1부 — 첫 10분(14장)
- **기획:** 처음 여는 사람을 위한 입구: 무엇인가, 어디서 받나, 부트스트랩, pkg, 저장소, 키보드, 비상 세션, 도움 받는 곳.
- **TC:** 조립 검사 오류 0건, 출처 없는 권고 2건 삭제, 원리는 3~9부로 넘기는 링크만.
- **개발:** `termux/deck/sections/01_first10min.html`, `termux/deck/claims.md`, `termux/PLAN.md`, `Termux_대백과사전.html`
- **검증:** make all SKEL=1 오류 0건 · 역검증 통과

---
## Archive
- [2026-09](history/archive/history-2026-09.md) — 93 entries
