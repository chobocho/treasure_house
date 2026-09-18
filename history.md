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

### [2026-09-18 05:18] Termux 대백과사전 덱 15부 — 문제 해결 사전(24장)
- **기획:** 화면의 오류 한 줄에서 출발해 메시지·원인·해결과 근거를 적는 18항목. 링커 오류는 실험으로 재현.
- **TC:** 실험 12 시험 3건(glibc 메시지·종료 코드·남은 파일, bionic 메시지, 사용법) 먼저 RED 확인 후 구현.
- **개발:** `termux/exp/missing_lib.sh`, `termux/exp/tests/test_exp.py`, `termux/run_all.py`, `termux/deck/sections/15_troubleshoot.html`, `termux/deck/claims.md` 외 5개 파일
- **검증:** test_exp·test_run_all 통과 · make all SKEL=1 오류 0건
- **비고:** 시계 오차 항목은 출처가 없어 뺐다. getprop 거부 원인은 미확인.

### [2026-09-18 05:14] Termux 대백과사전 덱 14부 — 보안과 개인정보(15장)
- **기획:** 위협 모델, 매니페스트의 문과 자물쇠, 2022년 공개된 앱 취약점 3건, 보안 정책, sshd 노출, 이 덱의 개인정보 규칙.
- **TC:** 캡처 2종(src_security·scrub_demo — 명령 줄이 검사에 안 걸리게 printf 로 조립), 조립 검사 오류 0건, 과장 문장 4건 정정.
- **개발:** `termux/deck/sections/14_security.html`, `termux/data/docs.tsv`, `termux/run_all.py`, `termux/out/` 2개, `termux/deck/claims.md`, `termux/PLAN.md`, `Termux_대백과사전.html`
- **검증:** test_run_all 통과 · make all SKEL=1 오류 0건 · 역검증 통과
- **비고:** termux-keystore·백업 암호화는 출처가 없어 다루지 않음.

### [2026-09-18 04:23] Termux 대백과사전 덱 12부 — 활용 III: GUI 와 데스크톱(11장)
- **기획:** Termux:X11·VNC·데스크톱을 문서와 소스로, 이 기기엔 X11 이 없다는 것과 이 세션이 /tmp 를 나누지 않았다는 것을 캡처로.
- **TC:** 캡처 x11_proot 추가(두 /tmp 의 inode·X 소켓 디렉터리), 조립 검사 오류 0건, 근거 없음 0건.
- **개발:** `termux/deck/sections/12_gui.html`, `termux/run_all.py`, `termux/out/x11_proot.txt`, `termux/deck/claims.md`, `termux/PLAN.md`, `Termux_대백과사전.html`
- **검증:** make all SKEL=1 오류 0건 · 역검증 통과
- **비고:** X11 패키지를 설치하지 않아 화면 그림 없음. GPU 가속 이후 변화는 미확인.

### [2026-09-18 04:20] Termux 대백과사전 덱 11부 — 활용 II: 자동화와 서버(13장)
- **기획:** runit 서비스, Termux:Boot 가 부팅 스크립트를 넘기는 길, 폰 위 웹 서버, NAT 너머 접속, 정해진 때 돌리기.
- **TC:** 실험 11 시험 3건(200·크기, 없는 파일 404, 사용법 오류, 끈 뒤 포트 비움) 먼저 작성해 RED 확인 후 구현.
- **개발:** `termux/exp/serve_once.sh`, `termux/exp/tests/test_exp.py`, `termux/run_all.py`, `termux/deck/sections/11_auto.html`, `termux/deck/claims.md` 외 4개 파일
- **검증:** test_exp·test_run_all 통과 · make all SKEL=1 오류 0건
- **비고:** 서비스를 켜거나 포트를 바깥에 열지 않았다. 서버는 127.0.0.1 에서 한 번 묻고 끔.

### [2026-09-18 04:15] Termux 대백과사전 덱 10부 — 활용 I: 개발 환경(18장)
- **기획:** 이 폰의 작업대: 깔린 도구와 판, 도구마다 자기를 어디서 도는 줄 아는지, 파이썬·Node·ssh·git·셸 설정.
- **TC:** 캡처 2종(dev_termux 스냅샷·dev_proot) 추가, 조립 검사 오류 0건, 출처 없는 문장 1건 삭제.
- **개발:** `termux/deck/sections/10_dev.html`, `termux/run_all.py`, `termux/out/dev_*.txt`, `termux/deck/claims.md`, `termux/PLAN.md`, `Termux_대백과사전.html`
- **검증:** test_run_all 통과 · make all SKEL=1 오류 0건 · 역검증 통과
- **비고:** Go·Rust 는 짓지 않고 판만(결정 10). 우분투 쪽엔 node·git 이 없어 Termux 것이 쓰였다는 사실을 캡처로 확인.

### [2026-09-18 04:11] Termux 대백과사전 덱 8부 — 한계와 우회(35장)
- **기획:** root·팬텀 프로세스·Doze·W^X·낮은 포트·저장소·서비스·이식·백업·키보드를 '무엇이 막나·이 기기·우회·대가' 순서로.
- **TC:** 조립 검사: 인용 범위 경계 통과, 캡처 등급 오류는 빌드 출력 캡처로 해소, 출처 없는 문장 4건 삭제.
- **개발:** `termux/deck/sections/08_limits.html`, `termux/deck/claims.md`, `termux/deck/pending.txt`, `termux/PLAN.md`, `Termux_대백과사전.html`
- **검증:** make all SKEL=1 오류 0건 · 역검증 통과
- **비고:** adb·root 가 필요한 우회는 실행하지 않고 문서를 인용. 몇 포트만 열리는 까닭은 미확인(네이티브 대기).

### [2026-09-18 04:11] Termux 덱 — 패치 통계 도구·8부 캡처 4종·데비안 판 오탐 수정
- **기획:** 8부 증거: 이 앱의 프로세스 수, termux-packages 의 패치 양, libandroid-* 메우개, 배터리 최적화 요청 소스를 캡처로.
- **TC:** 정상: 판별 패키지·패치·패치 있는 패키지 수와 상위 목록. 경계: .patch32 제외·작업 트리 변경 무시·없는 판·인자 없음. 판 문자열은 IP 아님.
- **개발:** `termux/tools/patch_stats.sh`, `termux/tools/tests/test_patch_stats.py`, `termux/tools/scrub.py`, `termux/tools/tests/test_scrub.py`, `termux/run_all.py`, `termux/out/` 외 5개 파일
- **검증:** make test 전부 통과 · 캡처 검사 0건 · 개인정보 검사 0건

### [2026-09-18 03:58] Termux 대백과사전 덱 9부 — proot 와 리눅스 배포판(45장)
- **기획:** ptrace·seccomp 로 호출을 가로채는 원리, proot-distro 가 조립하는 명령줄, 가짜 /proc·하드 링크 흉내, 못 속이는 벽.
- **TC:** 조립 검사: 인용 범위 52개 경계 통과, 소스 줄 인용 56건 핀 확인, 연도로 읽힌 숫자 1건 삭제.
- **개발:** `termux/deck/sections/09_proot.html`, `termux/deck/claims.md`, `termux/deck/src_used.txt`, `termux/PLAN.md`, `Termux_대백과사전.html`
- **검증:** make all SKEL=1 오류 0건 · 역검증 통과 · 267장
- **비고:** 하드 링크 흉내가 필요한 까닭·getprop 거부·API 무응답의 원인은 미확인 표시. 네이티브 비교값은 device.txt 대기.

### [2026-09-18 03:57] Termux 덱 — proot 캡처 4종·syscall_loop getcwd 모드·공용 DNS 허용
- **기획:** 9부 증거: 이 세션의 proot 명령줄·컨테이너·link2symlink·소스 사실을 캡처로, 가로채는 호출과 아닌 호출의 비용을 실험으로.
- **TC:** 정상: getcwd 모드 출력(양쪽 libc). 경계: N=0·모르는 모드·인자 초과 거부, 공용 DNS 유지·이웃 주소는 가림.
- **개발:** `termux/exp/syscall_loop.c`, `termux/exp/tests/test_exp.py`, `termux/tools/scrub.py`, `termux/tools/tests/test_scrub.py`, `termux/tools/native_facts.sh`, `termux/run_all.py`, `termux/out/` 외 N개 파일
- **검증:** make test 전부 통과 · 캡처 검사 0건 · 개인정보 검사 0건
- **비고:** syscall_loop.c 의 '모든 호출을 가로챈다' 주석은 소스(seccomp 필터)와 달라 바로잡았다.

### [2026-09-18 03:42] Git 대백과사전 덱 5단계 — Python mygit 1~12단계(시험 135 · 장면 20 통과)
- **기획:** SPEC 대로 SHA-1·zlib·객체·트리·커밋/참조·인덱스·log·diff·checkout·merge·팩·전송을 한 단계 한 커밋으로, 장면 실행기로 golden/scen 20개 재생.
- **TC:** 단계마다 "not implemented" 로 RED 확인 후 GREEN. git 커밋·태그·인덱스·색인 바이트 재현, diff 30쌍 바이트 일치, v2 대화 기록 일치.
- **개발:** `git/py/mygit/*.py`(16), `git/py/mygit/tests/*.py`(13), `git/SPEC.md`, `git/tools/golden_cases.py`, `git/golden/scen/diff.scn`, `git/PLAN.md`
- **검증:** 135 passed, 0 failed, 1 skipped(0444 를 못 지키는 파일 시스템) · 장면 20/20 · make all SKEL=1 오류 0건
- **비고:** 구현 3,462줄로 계획의 2.7배 — 다섯 언어 전문 게재 시 장수 초과 위험, 19부 전에 결정 필요.

### [2026-09-18 03:29] Termux 대백과사전 덱 7부 — Termux:API · 플러그인(24장)
- **기획:** termux-* 스크립트 → libexec/termux-api → 소켓 또는 am broadcast → 앱 수신기의 길, 개인정보 명령, 플러그인 여섯 개.
- **TC:** 조립 검사: 인용 범위 40개 경계 통과, 소스 줄 인용 45건 핀 확인, 캡처 등급 오류 3건을 캡처 추가로 해소.
- **개발:** `termux/deck/sections/07_api.html`, `termux/deck/claims.md`, `termux/deck/src_used.txt`, `termux/PLAN.md`, `Termux_대백과사전.html`
- **검증:** make all SKEL=1 오류 0건 · 역검증 통과 · 223장
- **비고:** 네이티브 API 출력은 사용자의 native_facts.sh 실행(data/device.txt)을 기다린다. proot 에서 API 가 멈추는 까닭은 미확인 표시.


---
## Archive
- [2026-09](history/archive/history-2026-09.md) — 82 entries
