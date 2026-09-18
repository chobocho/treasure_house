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

### [2026-09-18 01:17] Git 대백과사전 덱 2단계 — SPEC.md(다섯 mygit 의 약속)
- **기획:** 16절 규격서 — 객체·참조·인덱스·status·명령 출력·걷기·diff·merge·팩·전송·이름표·시험 배치.
- **TC:** 바이트 예시 9개를 진짜 git 으로 뜨는 spec_examples.py + make spec-check(9/9). diff 원형 1,500쌍 대조로 agree/tie 두 목록 결정.
- **개발:** `git/SPEC.md`, `git/tools/spec_examples.py`, `git/tools/gitenv.py`, `git/Makefile`, `git/deck/claims.md`, `git/PLAN.md`
- **검증:** make all SKEL=1 오류 0건 · spec-check 어긋남 0건 · width 0건
- **비고:** diff 는 git 과 같은 길이의 다른 스크립트를 고르는 경우가 있어 tie 쌍으로 따로 보인다. merge 기준은 git merge(ZEALOUS).

### [2026-09-18 01:14] Termux 대백과사전 덱 2단계 — tmx.sh 거부 목록·scrub.py·첫 캡처
- **기획:** 호스트 Termux 로 가는 유일한 문(tmx.sh)과 개인정보 필터(scrub.py), 캡처 틀(run_all.py)을 시험 먼저 만든다.
- **TC:** 정상: 허용 명령·끝줄·종료 코드·시간 초과. 가장자리: 거부 52종 미실행 증명·쓰기 우회·rm 경로·오탐(/root/TUR)·가린 보고.
- **개발:** `termux/tools/tmx.sh`, `termux/tools/scrub.py`, `termux/run_all.py`, `termux/tools/tests/*.py`(3), `termux/out/env_termux.txt`, `termux/PLAN.md`
- **검증:** 80 passed, 0 failed · make all SKEL=1 오류 0건 · env_termux md5 3회 동일
- **비고:** proot 에서 부른 Termux 바이너리도 ptrace 아래라 id·uname·getcwd 는 proot 값 — 네이티브 값은 device.txt 로 받는다.

### [2026-09-18 00:53] Termux 대백과사전 덱 1단계 — 뼈대(조립기·검사·34장)
- **기획:** transformer 조립기·검사를 복사해 대상·언어·상한 3000·근거 등급 5종만 바꾸고, CITE 를 핀 고정 upstream 소스 배지 SRC 로 교체.
- **TC:** 정상: srcpin 17건(핀 커밋 읽기·짧은 SHA). 가장자리: SHA 불일치·미등록 저장소·체크아웃 없음·파일 없음·빈 표 + scratch 연기 시험 오류 경로 8종.
- **개발:** `termux/deck/srcpin.py`, `termux/deck/build_deck.py`, `termux/deck/base/head.html`, `termux/deck/sections/*.html`(18), `termux/Makefile`, `termux/data/*.tsv`, `termux/PLAN.md` 외 21개 파일
- **검증:** 17 passed, 0 failed · make all SKEL=1 오류 0건 · 34장 · DeckMono 32 KB
- **비고:** 아이콘에 초록이 없어 배색은 termux-app 기본 16색(dim green)에서 잼. 브라우저 육안 확인 전, record.sh 는 6단계에서 고침.

### [2026-09-18 00:50] Git 대백과사전 덱 1단계 — 뼈대(조립기·검사·34장)
- **기획:** transformer 조립기·검사를 복사해 대상·5개 언어·상한 3000·CITE(형식 문서 표)만 바꾸고, 캡처 별칭 지시자 GIT 추가.
- **TC:** GIT 지시자(캡처 있음/없음/첫 줄 불일치)·CITE(표에 없는 키) 오류 경로를 scratch 에서 확인, gitenv.sh 로 커밋해 날짜 고정·전역 설정 차단 확인.
- **개발:** `git/Makefile`, `git/deck/build_deck.py`, `git/deck/base/head.html`, `git/deck/sections/*.html`(21), `git/tools/gitenv.sh`, `git/data/*.tsv`, `git/PLAN.md` 외 33개 파일
- **검증:** make all SKEL=1 오류 0건 · 34장 · 코드 블록 1개 일치 · DeckMono 28 KB
- **비고:** 배색 slate+git 주황 확정. typescript 5.9.3 설치·git/git 부분 복제 118 MB 완료. history.html 은 별도 커밋으로 회전.

### [2026-09-18 00:35] Termux 대백과사전 덱 계획서 — 상한 3000장·결정 12건 확정
- **기획:** 역사·원리·한계·활용을 18부 2,480장 예산으로 설계, Opus 빌더용 `termux/PLAN.md` 작성.
- **TC:** 계획 단계라 코드 없음. proot 에서 Termux bionic 바이너리(pkg·dpkg·termux-api) 실행 가능함을 실측으로 확인.
- **개발:** `termux/PLAN.md`
- **검증:** 부 예산 합 2,480 검산, 위키·GitHub·F-Droid 접속 200 확인, termux-app 최신 v0.118.3 API 대조
- **비고:** 실기기 캡처는 tools/tmx.sh 거부 목록 경유·개인정보 API 미실행. 기기 정보 `data/device.txt` 는 사용자가 native Termux 에서 붙여 넣어야 한다.

### [2026-09-17 00:08] 트랜스포머 카드 퀴즈 수 정정 — 46 → 45
- **기획:** 3차 리뷰에서 "검사기 45개 vs 실제 46개" 로 남긴 건의 원인 조사.
- **TC:** 조립된 덱에서 <script> 를 뺀 뒤 `card quiz` 를 세어 45개 확인, 46번째는 demos.js 안 주석 한 줄.
- **개발:** `index.html`, `README.md`, `transformer/PLAN.md`
- **검증:** 검사기 출력 "퀴즈 45개" 와 카드 설명 일치
- **비고:** 검사기는 옳았고 카드 설명이 틀렸다. 덱을 grep 으로 셀 때는 스크립트를 빼야 한다.

### [2026-09-16 23:37] 트랜스포머 덱 3차 리뷰 — 43건 정정
- **기획:** 1·2차와 다른 각도 — 초심자 독해 흐름(정의 전 사용·"앞에서 본" 실재 여부·목차 순서), 산문↔코드 조각·캡처 일치, 파이썬·C 주석 정확성, 한국어 표기·문체.
- **TC:** 보고 전용 서브에이전트 2개(0~6부+py 주석, 7~14부+C 주석)의 39건을 전부 소스·캡처와 대조해 확인, 기계 검사로 문체 3건·카드 1건 추가.
- **개발:** `transformer/deck/sections/*.html`(11), `transformer/c/main.c`, `transformer/c/model.c`, `transformer/py/transformerlib/ops.py`, `py/transformerlib/posenc.py`, `py/transformerlib/tokenizer.py`, `index.html`, `README.md`
- **검증:** make all 종료 0 · 파이썬 시험 188 통과 · C 확인 561건 통과 · 흐름 14·코드불일치 5·주석 7·표기 17
- **비고:** 4부 퀴즈 두 장을 묻는 장 끝으로 옮김. 카드의 "논문 53편 절 단위 인용"은 색인 53편·절 인용 49편으로 정정.

### [2026-09-16 22:41] 트랜스포머 덱 2차 리뷰 — 33건 정정
- **기획:** 1차와 다른 각도 — 본문 계산·퀴즈 답 재계산, 부를 넘는 기호 일관성, "N부에서 다룬다" 약속, 그림 23장 렌더 확인, 용어집 id.
- **TC:** 데모 7종을 무작위 입력 1,800개로 파이썬과 대조(불일치 0), 문서 안 덧셈 모델은 경계 포함 308문제를 C 와 대조(불일치 0).
- **개발:** `transformer/deck/sections/*.html`(9), `deck/glossary.txt`, `deck/gen_figs.py`, `py/demo/demo_kvcache.py`, `py/demo/demo_optim.py`, `out/`, `PLAN.md`
- **검증:** make all 종료 0 · 파이썬 시험 188 통과 · 사실오류 3·수식 4·인용범위 4·표기 22
- **비고:** KV 캐시 한 토큰 비용 n·d → 2·n·d 정정, 용어집 중복 3쌍 병합으로 181개.

### [2026-09-16 16:08] 트랜스포머 덱 완성·공개 — 952장(2~13단계)
- **기획:** PLAN.md §5 2~13단계 — SPEC, 순수 파이썬 참조 13모듈, C99 재구현, 기록 실행, 그림·본문·데모, 공개, 리뷰 1차.
- **TC:** 파이썬 시험 188개·C 확인 561건(로짓·기울기·20스텝 손실·토큰 바이트 대조), 데모 사례 22건, 문서 안 추론 1000문제 C 대조.
- **개발:** `transformer/py/`, `transformer/c/`, `transformer/py/demo/`, `transformer/deck/sections/*.html`, `transformer/deck/demos.js`, `transformer/tools/export_js.py`, `index.html`, `README.md` 외 다수
- **검증:** make all 종료 0 · record --check 캡처 36개 3회 md5 동일 · 리뷰 40건 정정(1a7927f)
- **비고:** 홀짝 과제는 배우지 못해(48.1 %) 손실 바닥 셈과 함께 실패로 실었다. 과제 학습 일부가 3분 예산을 넘는다(PLAN 7단계).

### [2026-09-16 12:10] 트랜스포머 덱 1단계 — 뼈대(조립기·검사·28장)
- **기획:** 무선통신 덱 조립기·검사를 복사해 대상 파일·언어(py+C)·커버리지·상한 2000장만 바꾸고, SPEC 지시자를 논문 절 배지 CITE 로 교체. 배색은 "먹과 종이".
- **TC:** 뼈대 단계라 단위 시험 없음. 역검증에 "조립기를 거치지 않은 논문 배지" 검사를 새로 넣었고 첫 빌드에서 손으로 쓴 예시 배지 1건을 잡았다.
- **개발:** `transformer/deck/build_deck.py`, `deck/check_claims.py`, `deck/verify_deck.py`, `deck/base/head.html`, `Makefile`, `deck/sections/*.html`(15), `data/*.tsv`(4) 외 12개 파일
- **검증:** make all SKEL=1 오류 0건 · 28장 · xref 14 · check_deck 11/11 · 글꼴 DeckMono 29 KB 통과
- **비고:** 계획서의 "~30장" 은 28장(부 표지 한 장씩 유지). 본문은 지시대로 합니다체. index/README 카드는 공개 단계에서.

### [2026-09-16 11:59] 트랜스포머 덱 — 작업 지시서 작성(transformer/PLAN.md)
- **기획:** 밑바닥부터 만드는 트랜스포머 덱을 Opus 가 짓도록 영문 지시서를 썼다. 무선통신 덱 조립기·검사와 최적화 덱 수식 키트를 물려받고, 상한 2000장·목표 1,400~1,800장·15부 예산 약 1,575장.
- **TC:** 지시서 단계라 시험 없음. 못 박은 유일한 숫자 GPT-2 small 파라미터 수 124,439,808 은 계산으로 검산.
- **개발:** `transformer/PLAN.md` — 원칙 12·모듈 13(py)+8(c)·증인 시험·수식 정책·작업 순서 13단계·부별 예산·완료 기준·결정 9건.
- **검증:** 인코딩 이상 0건, 결정 9건 사용자 확정(cb0ef08).
- **비고:** numpy 없이 순수 파이썬 참조 + C99 재구현이 SPEC.md 의 난수·체크포인트·BPE 규칙을 공유해 서로 대조한다. 코퍼스는 합성 과제 + ko.wikisource 공유저작물. index/README 카드는 공개 단계에서.

### [2026-09-16 09:50] 무선통신 덱 3차 리뷰 — 42건 정정 (871장)
- **기획:** 1·2차와 다른 각도 — 슬라이드 위의 증거(코드·캡처·그림·인용 조항·표)가 옆 산문과 같은 말을 하는지. 서브에이전트 둘이 0~7부·8~15부, 데모 12종은 격자 1,420점으로 파이썬과 직접 대조(불일치 0).
- **TC:** `harq.utilization` 시험 4건 RED→GREEN(정지 대기 12.5 %·8프로세스 100 %·슬롯 모사 일치·범위 예외). `make all`·`record --check` 3회 md5 동일이 관문.
- **개발:** `deck/sections/*.html`(13), `deck/gen_figs.py`, `py/wirelesslib/harq.py`, `py/demo/*.py`(10), `data/generations.tsv`, `data/timeline.tsv`, `deck/claims.md`, `deck/glossary.txt` 외 4개 파일
- **검증:** 335 passed, 0 failed · make all 오류 0건(871장·그림 30장 일치·데모 동작 31건·조항 55건 근거 없음 0)
- **비고:** 그림 13·캡처-산문 7·인용조항 7·표기 6·사실오류 3·퀴즈 3·코드-산문 2·표 1·용어집 1. 캡처가 재현되고 시험을 통과해도 슬라이드가 엉뚱한 절을 가리킬 수 있었다(HARQ N-프로세스). 3GPP 창립은 5기구(CWTS 는 1999-06 합류)로 바로잡았다.

### [2026-09-16 08:30] 무선통신 덱 2차 리뷰 — 47건 정정 (870장)
- **기획:** 1차와 다른 각도로 — 한 서브에이전트는 산문의 모든 수치를 독립 재계산, 다른 하나는 되짚기·중복·용어집·퀴즈 정합. 1차가 손으로 찾던 결함은 먼저 기계 검사로 승격했다.
- **TC:** 조립기에 "실행 검증 배지인데 화면에 근거가 없다" 검사를 넣어 16장을 잡았고, `make all` 전체가 관문이다.
- **개발:** `deck/build_deck.py`, `deck/sections/*.html`(16), `deck/glossary.txt`, `data/timeline.tsv`, `index.html`, `README.md`
- **검증:** make all 오류 0건 — 870장, 데모 동작 31건, 규격 조항 51건·연도 207건 근거 없음 0건, 커버리지 100 %
- **비고:** 1차 수정이 만든 오류가 하나 있었다(정지궤도 EIRP 에 송신 이득을 이중으로 셈). 고치는 것도 바꾸는 것이라 같은 검산이 필요하다. 계산해 두고 본문에서 한 번도 안 쓰던 캡처 아홉 절도 슬라이드로 올렸다.

### [2026-09-16 07:40] 무선통신 덱 12단계 — 전수 리뷰 36건 정정
- **기획:** PLAN §5 12단계. 서브에이전트 둘이 0~7부·8~15부를 소스·캡처·규격 원문과 대조하고, 보고된 것은 전부 직접 재검증한 뒤 고쳤다.
- **TC:** `make all` 전체가 관문 — 조립·역검증·데모 동작 31건·규격 조항 51건·연도 203건.
- **개발:** `deck/sections/*.html`(12), `deck/demos.js`, `deck/check_deck.js`, `deck/build_deck.py`, `deck/glossary.txt`, `wireless/PLAN.md`
- **검증:** make all 오류 0건 — 864장, 데모 동작 31건 일치, 근거 없는 연도·조항 0건
- **비고:** 사실오류 12·수식 3·인용범위 9·표기 12·모순 3·용어집 1. 가장 뼈아픈 것은 데모가 바로 앞 슬라이드에서 "고쳤다" 고 적은 버그를 그대로 재현하던 것(GEO 도플러 3.1 kHz)이었다 — 식을 옮기면 그 식의 역사도 같이 옮겨야 한다.

### [2026-09-16 07:05] 무선통신 덱 11단계 — 공개 (864장, index·README 갱신)
- **기획:** PLAN §5 11단계. 글꼴 내장·장수 세기·카드 추가를 한 커밋으로 묶었다(저장소 관례).
- **TC:** `make font-check` 와 `deck-check` 의 장수·id 유일성 검사가 관문이다.
- **개발:** `index.html`, `README.md`, `무선통신_대백과사전.html`
- **검증:** make all 오류 0건 — 864장·2,224 KB, 규격 조항 53건·연도 200건 근거 없음 0건, 63개 파일 72칸 이내, DeckMono 내장·검사 통과
- **비고:** 장수는 빌드 출력에서 세어 적었다. 카드 설명의 수(모듈 18·6,442줄·시험 331·규격 41편·데모 12·퀴즈 30·용어집 267)도 전부 실측값이다.

### [2026-09-16 06:55] 무선통신 덱 9·10단계 — 데모 12개·용어집 267낱말·부록 소스 전문
- **기획:** 데모는 파이썬 참조와 같은 식을 쓰고, 기댓값은 파이썬이 낸 값만 적는다(자기 출력을 적으면 검사가 아니다).
- **TC:** `check_deck.js` CASES 28건 — 전부 `py/wirelesslib` 가 낸 값. 빈 입력에서 죽지 않는지도 12개 전부 확인.
- **개발:** `wireless/deck/demos.js`, `deck/check_deck.js`, `deck/glossary.txt`, `deck/sections/15_appendix.html` 외 7개 파일
- **검증:** 데모 12개 스텁 통과·동작 28건 일치, 용어집 화살표 267개 전부 실재, 소스 커버리지 6,442/6,442줄(100 %)
- **비고:** 데모 안에 `<select>` 를 쓰면 챕터 이동 검사가 `<option value>` 를 슬라이드 id 로 읽어 가짜 오류를 낸다. 입력칸으로 바꿨다.

### [2026-09-16 06:30] 무선통신 덱 8단계 후반 — 8~15부 본문 (표준화·3G·4G·5G·NTN·6G·비교)
- **기획:** 규격 조항 배지를 실제로 받아 둔 `specs/*.txt` 로 검사하게 하고, 2025년 이후는 전부 "2026-09 기준" 을 박았다.
- **TC:** `make claims-check` — 조항이 규격 본문에 있는지·연도에 근거가 있는지. 8부를 쓰며 없는 조항 인용 1건을 잡아 고쳤다.
- **개발:** `deck/sections/{08_standards,09_umts,10_lte,11_nr,12_ntn,13_6g,14_compare}.html`, `deck/claims.md`, `tools/fetch.sh`, `deck/check_claims.py`
- **검증:** make all SKEL=1 오류 0건 — 규격 조항 인용 53건·연도 200건 근거 없음 0건
- **비고:** `tools/fetch.sh` 와 `check_claims.py` 의 긴 줄을 72칸에 맞춰 접었다. 덱에 인용해 실으려면 폭 규칙을 지켜야 하는데, 도구 자신이 그것을 어기고 있었다.

### [2026-09-16 05:30] 무선통신 덱 8단계 전반 — 1·4·5·6·7부 본문 (여명·다중접속·1G·GSM·CDMA)
- **기획:** 수식의 뼈대(0·2·3·4부)를 먼저 세운 뒤 역사와 세대를 썼다. 날짜는 전부 `data/timeline.tsv` 에서 가져온다.
- **TC:** 조립기의 폭·근거 등급·상호참조 검사에 더해 `check_claims.py` 가 연도마다 근거를 요구한다.
- **개발:** `deck/sections/{01_dawn,04_access,05_1g,06_gsm,07_cdma}.html`, `deck/build_deck.py`, `data/timeline.tsv`, `deck/claims.md`, `deck/years_ok.txt`
- **검증:** make all SKEL=1 오류 0건 — 슬라이드 378장 시점까지 누적 무결
- **비고:** 자유 라이선스 검사가 대소문자를 가려 `'Public domain'` 사진을 거절했다. 공용이 돌려주는 이름이 들쭉날쭉하므로 소문자로 낮춰 견주도록 고쳤다. 1902년 헤비사이드·케넬리 반사층은 근거 행을 새로 만들었다.

### [2026-09-16 02:55] 무선통신 덱 1단계 — 뼈대(조립기·검사·부 표지 29장)
- **기획:** 압축 덱의 조립기·검사 일곱 개와 최적화 덱의 CSS 수식 키트를 물려받고, 이 덱에만 필요한 지시자 셋(TABLE·PHOTO·SPEC)과 사실 검사 하나를 새로 붙였다.
- **TC:** 조립기 자체 검사가 시험 노릇을 한다 — 폭·근거 등급·커버리지·상호참조·용어집 화살표·자기완결형에 더해, 규격 번호가 표에 없거나 사진이 자유 라이선스가 아니면 조립이 멈추게 했다.
- **개발:** `wireless/Makefile`, `wireless/deck/{build_deck,verify_deck,gen_tables,check_claims}.py`, `wireless/deck/base/head.html`, `wireless/deck/sections/*.html`(16), `wireless/data/*.tsv`(7) 외 12개 파일.
- **검증:** `make all SKEL=1` 오류 0건 — 29장·고유 id 29개·152 KB, 역검증 통과, 상호참조 15개 정상, DeckMono 30 KB 내장·검사 통과, `make width` 통과.
- **비고:** 부 표지를 일부러 한 장씩만 두었다 — 두 장이면 조립기가 "이미 쓴 부" 로 세어 남은 예산 합계(2,580장)가 0 으로 나온다. index.html·README 카드는 지시서대로 아직 안 붙였다.
### [2026-09-16 02:33] 무선통신 대백과사전 덱 — 작업 지시서 작성(wireless/PLAN.md)
- **기획:** 1G AMPS·모토롤라부터 GSM·CDMA·UMTS·LTE·5G·6G·위성 NTN 까지 16부, 상한 3000장(목표 2,300~2,700). 압축 덱 조립기·검사와 최적화 덱 CSS 수식 키트를 재사용하고, 순수 파이썬 시뮬레이션 18모듈이 모든 수식·숫자의 증거가 된다.
- **TC:** 해당 없음(지시서 단계). 수식마다 이론값 대조 시험을 두는 규칙(§0-3)과 사실마다 출처를 먼저 적는 규칙(§0-4)을 지시서에 못 박았다.
- **개발:** `wireless/PLAN.md`, `wireless/tools/fetch.sh`, `wireless/tools/sectigo_ov_r36.pem`, `.gitignore`.
- **검증:** 3gpp.org 는 중간 인증서 누락으로 curl·WebFetch 가 실패하던 것을 fetch.sh 로 해결 — 릴리스 페이지·38 시리즈 목록·38211-i60.zip 내려받고 .docx 조항 제목 추출 확인.
- **비고:** 사용자가 §9 권장안(파일명·사진 base64 내장·파이썬 단일 코드층·한국 시장 관통 서사·스펙은 읽는 법 중심·Wi-Fi 교차 링크) 전부 승인. 다음은 Opus 가 §5 1단계(뼈대)부터.
### [2026-09-13 01:17] 압축 덱 4차 리뷰 — 사실오류 43건·퀴즈 3건·인용범위 5건·표기 7종·잠재 코드 결함 1건 정정
- **기획:** 1~3차가 숫자·부록·용어집을 봤으므로 4차는 산문을 소스 옆에 두고 "설명이 코드와 다른 자리"를 정독(서브에이전트 2개, 1~7부/8~14부)하고, 퀴즈 19개 정답·소수 비율·도해 28장 글자·데모 설명을 기계와 손으로 대조했다.
- **TC:** 지적마다 코드를 실제로 돌려 재확인 — LZW 사전 크기(abab 384)·CLEAR 횟수, zlib 레벨 1 토큰(거리 258), BWT 옛 키의 왕복 실패, DCT 오차 2, 카운터 색인, jpeglite 37×40 기댓값. 파이썬 시험에 그 기댓값을 추가(250개).
- **개발:** `compress/deck/sections/00~14`, `compress/src/py/compresslib/` lossy·huffman·lzss·bwt·rangecoder, `compress/src/{cpp,go,java,ts}` lossy·rle 주석, `compress/deck/gen_figs.py`, `compress/SPEC.md` 외 3개 파일.
- **검증:** make all 오류 0건 · 1,478장 유지 · 파이썬 250 passed · C++ 141 · 자바 134 · Go OK · TS 14 pass · lossy 파서티 실패 0건 · 폭 159파일 통과.
- **비고:** jpeglite 부호기의 0런 분할이 (254,0) 뒤에 254 를 빼 복호기(255)와 한 칸 어긋났다 — 8×8 에서는 닿지 않는 자리라 출력은 그대로. 다섯 언어 모두 255 로 고쳤다.
### [2026-09-12 19:55] 부록 연속성 검사를 make all 에 붙임 — deck/check_appendix.py
- **기획:** 3차 리뷰에서 쓰던 검사가 `scratch/` 에만 있어 다음 사람이 모른다. 커버리지는 "덱 어딘가에 실렸는가" 만 보므로 본문 인용이 메워 주면 부록에 구멍이 나도 100% 다 — 그 빈틈을 메우는 검사라 조립 흐름에 넣었다.
- **TC:** RED 둘 — 덱의 조각 범위를 28–67 → 29–67 로 흔드니 "1–27 다음이 29–67" 로 잡혔고, FULLSRC 한 줄을 지우니 조립기의 커버리지가 먼저 잡았다(48줄 누락). 되돌린 뒤 GREEN.
- **개발:** `deck/check_appendix.py`(A1 첫 줄 · A2 끝 줄 · A3 빈틈·겹침 · A4 조각 번호 · A5 조각 제목의 이름이 그 코드에 있는가) · `Makefile`(deck-appendix 목표, all 에 편입).
- **검증:** `make all` 오류 0건 · 부록 143파일·제목 626개 어긋남 0건 · 1,478장 유지 · 파이썬 249 passed, 0 failed.
- **비고:** Makefile 이 7줄 늘자 부록 표지 줄 수가 23,915 → 23,922 로 저절로 따라갔다 — 바로 앞 커밋의 SRCSTAT 이 값을 한 자리다.

---
## Archive
- [2026-09](history/archive/history-2026-09.md) — 49 entries
