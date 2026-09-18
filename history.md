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

### [2026-09-18 03:28] Termux 덱 — termux-* 명령 색인 도구·API 소스 캡처·거부 캡처
- **기획:** 7부 표를 손으로 적지 않도록 캡처 두 개(주인 패키지·termux-api 호출)에서 84줄 색인을 만든다.
- **TC:** 정상: 행 수·주인·needs-app·privacy 분류. 경계: 빈 캡처·모르는 명령·주석 줄·정렬 고정(7건).
- **개발:** `termux/tools/api_table.py`, `termux/tools/tests/test_api_table.py`, `termux/run_all.py`, `termux/deck/gen_tables.py`, `termux/data/api_cmds.tsv`, `termux/out/` 캡처 6개
- **검증:** make test 192 passed, 0 failed · stable 캡처 재현
- **비고:** 개인정보 명령은 실행하지 않고 소스에서 칸 이름만 읽는다. tmx_deny 는 실행 전 거부(99)를 캡처.

### [2026-09-18 03:13] Termux 대백과사전 덱 6부 — 패키지 시스템(37장)
- **기획:** 폰의 pkg·apt·dpkg 에서 저장소·미러·키를 거쳐 termux-packages 공장과 부트스트랩까지, 그리고 .deb 손으로 만들기.
- **TC:** 조립 검사: 인용 범위 36개 경계 통과, 소스 줄 인용 40건 핀 확인, 출처 없는 문장 1건 삭제·1건 미확인 표시.
- **개발:** `termux/deck/sections/06_packages.html`, `termux/deck/claims.md`, `termux/deck/pending.txt`, `termux/PLAN.md`
- **검증:** make all SKEL=1 오류 0건 · 역검증 통과 · check_slices 어긋남 0건
- **비고:** 설치본 pkg 가 소스와 첫 줄만 다른 까닭을 massage 단계의 셔뱅 고치기로 확인. proot 에서는 pkg·apt 모두 root 거부.

### [2026-09-18 03:05] Termux 대백과사전 덱 4부 — 앱(32장)
- **기획:** termux-app 의 구조·터미널 에뮬레이터·PTY·TermuxService·부트스트랩·sharedUserId·RUN_COMMAND·properties·targetSdk 를 소스로.
- **TC:** 조립 검사: 인용 범위 26개 경계 통과, 소스 줄 인용 30건 핀 커밋 확인, 긴 줄은 캡처로 돌림.
- **개발:** `termux/deck/sections/04_app.html`, `termux/deck/claims.md`, `termux/PLAN.md`
- **검증:** make all SKEL=1 오류 0건 · 역검증 통과 · check_slices 어긋남 0건
- **비고:** ~/.termux 는 이름만 캡처(내용은 사용자의 것). 목표 170장 대비 32장 — 늘리지 않음.

### [2026-09-18 02:55] Termux 대백과사전 덱 5부 — 파일시스템과 실행(47장)
- **기획:** $PREFIX·셔뱅·termux-exec·W^X·시스템 링커 실행·paths.h·RUNPATH 를 핀 고정 소스와 캡처로.
- **TC:** 조립 검사: 근거 등급 a12·s13·b12, 인용 범위 18개 경계 통과, 연도 4건 근거 확인.
- **개발:** `termux/deck/sections/05_filesystem.html`, `termux/deck/claims.md`, `termux/PLAN.md`
- **검증:** make all SKEL=1 오류 0건 · 역검증 통과 · check_slices 어긋남 0건
- **비고:** 이 셸의 SELinux 문맥 untrusted_app_27 이 targetSdk 28 이 W^X 를 피하는 까닭의 직접 증거. 네이티브 셔뱅 결과는 device.txt 대기.

### [2026-09-18 02:38] Termux 대백과사전 덱 3부 — 안드로이드 위의 리눅스(54장)
- **기획:** 앱 샌드박스·uid·앱 데이터·bionic·SELinux·seccomp·Zygote·권한·스코프드 스토리지를 캡처·소스·공식 문서로.
- **TC:** 조립 검사: 근거 등급 a13·s5·b17, 코드·캡처 역검증 일치, 인용 범위 3개·연도 3건 근거 확인.
- **개발:** `termux/deck/sections/03_android.html`, `termux/deck/claims.md`, `termux/data/docs.tsv`, `termux/PLAN.md`
- **검증:** make all SKEL=1 오류 0건 · 역검증 통과 · claims-check 근거 없음 0건
- **비고:** proot 는 uid 를 0 으로 꾸미지만 보조 그룹(u0_a123_cache)이 앱 번호 123 을 드러낸다. 목표 160장 대비 54장 — 늘리지 않음.

### [2026-09-18 02:28] Termux 대백과사전 덱 6·7단계 — 캡처 26종(stable 20개 3회 동일)·그림 18장
- **기획:** 실기기 캡처를 stable/snapshot 으로 나눠 run_all 에 모으고, 구조도·자료 그림을 data/·out/ 에서 그린다.
- **TC:** 정상: record.sh 가 stable 만 대조·네이티브 파일 들여오기. 가장자리: snapshot 은 흔들려도 통과·흔들리는 stable 은 파일 이름과 함께 실패.
- **개발:** `termux/run_all.py`, `termux/tools/record.sh`, `termux/exp/{build,pkg_diff}.sh`, `termux/out/*.txt`(26), `termux/deck/gen_figs.py`, `termux/deck/figs/*.svg`(18)
- **검증:** 177 passed, 0 failed · make record stable 20개 3회 동일 · make all SKEL=1 오류 0건
- **비고:** Termux apt 가 uid 0 을 거부해 결정 5 의 설치는 불가 — 호스트 무변경. API·getprop 은 네이티브 스크립트로.

### [2026-09-18 02:24] Git 대백과사전 덱 4단계 — 조사(공식 문서·연표 126·CVE 40·출처 대장)
- **기획:** v2.55.0 태그의 공식 문서 943개와 메일 3통을 docs/ 로, 릴리스·CVE·연표·기여자·명령·자람 표를 mirror 에서 뽑는 make_data.py.
- **TC:** make data-check 로 생성 표 재현 확인, check_claims 에 formats.tsv 절 제목 존재 검사(32행) 추가. 외부 사실 13건은 원문을 curl 로 받아 문장 대조.
- **개발:** `git/tools/fetch_docs.py`, `git/tools/adoc_text.py`, `git/tools/make_data.py`, `git/data/*.tsv`(14), `git/deck/claims.md`, `git/deck/check_claims.py`, `git/Makefile`, `git/PLAN.md` 외 12개 파일
- **검증:** make all SKEL=1 오류 0건 · data-check 어긋남 0건 · 형식 표 32행 근거 확인
- **비고:** 1차 출처가 없는 "GitHub 창업일"·"2005-04-03 개발 시작"은 싣지 않기로 함. 날짜가 둘인 사건(Hamano 7-26/27, Mercurial 4-19/20)은 시간대 차이로 원문에서 확인.

### [2026-09-18 01:58] Termux 대백과사전 덱 5단계 — 실험 10종(bionic·glibc 두 번 짓기)
- **기획:** 같은 C 소스를 Termux clang(bionic)과 proot gcc(glibc)로 지어 차이를 보이고, 스크립트 실험으로 셔뱅·.deb·시그널·웨이크락을 다룬다.
- **TC:** 정상: 인사 줄 같음·interp 다름·u0_a123·빈 포트 한 줄·137. 가장자리: 사용 중 포트·잘못된 인자·실패해도 웨이크락 해제.
- **개발:** `termux/exp/*.c`(5), `termux/exp/*.sh`(4), `termux/exp/shebang/`, `termux/exp/mkdeb/`, `termux/exp/timeit_exp.py`, `termux/exp/tests/test_exp.py`, `termux/tools/native_facts.sh`
- **검증:** 166 passed, 0 failed · make all SKEL=1 오류 0건
- **비고:** 이 기기에서 1024 미만 포트는 20–23·80·443·445·515·631 만 bind 된다(원인 미확인). proot 안에서는 /tmp·/bin/sh 가 보여 네이티브 캡처가 필요.

### [2026-09-18 01:49] Termux 대백과사전 덱 4단계 — elf.py·deb.py·pkgstat.py
- **기획:** 5·6부가 쓸 표준 라이브러리 도구 셋: ELF 링커 정보, .deb 해부, dpkg status 통계.
- **TC:** 정상: 손으로 지은 ELF·.deb 와 readelf·dpkg-deb 대조. 가장자리: 32비트·빅 엔디언·정적·잘림·zst·크기 없는 패키지·빈 입력.
- **개발:** `termux/py/elf.py`, `termux/py/deb.py`, `termux/py/pkgstat.py`, `termux/py/tests/*.py`(3)
- **검증:** 146 passed, 0 failed · make all SKEL=1 오류 0건
- **비고:** 기기의 설치 패키지는 170개(계획서의 326 은 줄 수였다). Termux bash 는 linker64·RUNPATH $PREFIX/lib.

### [2026-09-18 01:44] Termux 대백과사전 덱 3단계 — upstream 26개 핀·문서 127건·자료표·주장 49건
- **기획:** 기억 대신 출처로: 저장소는 커밋, 위키는 revid, HTML 은 원문 해시로 핀 고정하고 연표·안드로이드 동작·릴리스를 표로 만든다.
- **TC:** 정상: fetch_src 8·doc_text 21·gh_api 7·native_facts 5. 가장자리: 위키 절 번호 중복·SHA 속 숫자의 IMEI 오탐을 시험으로 먼저 박음.
- **개발:** `termux/tools/{fetch_src.sh,doc_text.py,gh_api.py,native_facts.sh}`, `termux/data/*.tsv`(10), `termux/deck/claims.md`, `termux/PLAN.md`
- **검증:** 104 passed, 0 failed · make all SKEL=1 오류 0건 · 연표 81행·안드로이드 19행
- **비고:** targetSdk 는 v0.66(2019-01)부터 28, minSdk 는 v0.76 에서 24 인데 README 는 v0.83(태그 없음)이라 적는다. device.txt 는 사용자 실행 대기.

### [2026-09-18 01:43] Git 대백과사전 덱 3단계 — golden/(진짜 git 이 만든 기준 바이트 305개)
- **기획:** 입력·명령만 적은 golden_cases.py 를 git 2.55.0 에 돌려 기대값을 받는 make_golden.py, 다섯 언어가 같이 읽을 장면 파일(.scn) 형식을 SPEC §16.4 에 추가.
- **TC:** SHA-1 100·트리 12·diff 33쌍(agree 30/tie 3)·장면 19·팩 2·pkt 대화 3·오류 18. 저장 블록 객체가 git fsck --strict 통과.
- **개발:** `git/tools/make_golden.py`, `git/tools/golden_cases.py`, `git/golden/`(305파일), `git/SPEC.md`, `git/PLAN.md`
- **검증:** make golden-check 어긋남 0건(두 번 생성) · make all SKEL=1 오류 0건
- **비고:** 재료에 공백이 있으면 조용히 잘리던 결함을 커밋 전에 잡아 생성기가 거부하게 함.


---
## Archive
- [2026-09](history/archive/history-2026-09.md) — 71 entries
