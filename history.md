### [2026-09-21 06:38] 웹 인증 완전 가이드 덱 — 9쪽 뒤 ←→ 먹통 수정
- **기획:** 엔진이 INPUT·BUTTON 포커스면 ←→를 무시 — 9쪽 체크박스나 화면 버튼을 누르면 이후 키가 안 먹음.
- **TC:** 정상: 체크박스·다음 버튼 포커스에서 ←→ 이동. 경계: 텍스트칸에선 안 넘김, 체크박스 위 스페이스는 체크에 양보.
- **개발:** `웹_인증_완전_가이드.html`
- **검증:** DOM 스텁 8항목 수정 전 실패 5·수정 후 전부 통과 · embed_mono --check 통과

### [2026-09-19 11:31] Git 대백과사전 덱 전수 리뷰 3차 — 68건 정정·도구 3종 수정, 1830장
- **기획:** 1·2차가 안 본 "본문 정독 대 증거" — 0·12·14·15·16·18부는 직접, 나머지는 서브에이전트 여섯(둘씩)이 진짜 git 2.55 로 확인하며 읽음.
- **TC:** 정상: 새 캡처 넷(git 이 쓴 느슨한 객체 78 01·진짜 이름 바꾸기의 --follow 유무·커밋이 부르는 maintenance run --auto). 경계: SKEL=1 없는 make all, 뜻풀이 속 `<`·`#`, release: 자리표 날짜 풀이.
- **개발:** `git/deck/sections/`(18개), `git/deck/glossary.txt`, `git/deck/check_deck.js`, `git/deck/gen_glossary.py`, `git/deck/gen_tables.py`, `git/tools/make_data.py`, `git/exps/`(7개), `git/data/`(4개) 외 out·index·README
- **검증:** make all 오류 0건(SKEL=1 없이) · record 1,244 ×3 같음 · data-check 통과 · 1830장
- **비고:** 사실 12·불일치 17·모순 6·낡음 2·교차참조 17·한국어 13(fast-forward 를 "되감기" 로 옮긴 33곳 포함)·보강 1. 카드 숫자 퀴즈 61→60.

### [2026-09-19 08:51] Termux 덱 전수 리뷰 5차 — 가명 누출 1건 포함 29건 정정, 604장
- **기획:** 리뷰를 받은 적 없는 네이티브·가명 처리 14장과 0~8부·9~17부 3회차 정독(서브에이전트 둘), 기계 검사·그림은 직접.
- **TC:** 정상: 앱 이름 둘일 때 멱등, 가짜와 같은 진짜 번호가 연쇄로 안 바뀜. 경계: 접힌 줄에서 쪼개진 all_aN·덜 바뀐 미러를 check 가 잡음(값은 안 찍음).
- **개발:** `termux/tools/anon.py`, `termux/run_all.py`, `termux/tools/tests/`(2개), `termux/out/native_device.txt`, `termux/deck/sections/`(15개), `termux/deck/claims.md`, `termux/deck/glossary.txt`, `termux/exp/`(주석 2개) 외 5개 파일
- **검증:** make test 238 passed, 0 failed · make all 오류 0건 · 604장
- **비고:** 누출됐던 all_a 이름은 이전 두 커밋의 이력에 남아 있음 — 이력 재작성은 사용자 결정 대기.

### [2026-09-19 06:03] Termux 덱 앱 번호·미러 가명 처리 — 모든 캡처에서 가짜 값으로
- **기획:** 네이티브 캡처에 이어 예전 캡처의 uid·gid·SELinux 범주·미러도 가짜로. 진짜 번호는 소스에 적지 않고 u0_aN 모양으로 찾음.
- **TC:** 정상: uid·gid 셋·MCS 범주가 가짜 번호 123 으로 일관. 경계: 앱 이름 없는 파일은 그대로, 시스템 gid·TUR 유지, 두 번 불러도 같음.
- **개발:** `termux/tools/anon.py`, `termux/run_all.py`, `termux/tools/tests/`(2개), `termux/out/`(7개), `termux/deck/sections/`(6개), `termux/deck/claims.md`, `termux/deck/glossary.txt` 외
- **검증:** 단위 테스트 전부 통과 · make all 오류 0건 · 603장
- **비고:** git 이력과 보관 기록(history/archive)에는 예전 값이 남아 있음.

### [2026-09-19 04:39] Termux 덱 네이티브 캡처 반영 — device.txt 로 0·3·5·7·8·9부 11장 추가
- **기획:** 사용자가 네이티브 Termux 에서 뜬 device.txt 로 '공개 시점까지 오지 않았다' 자리를 실제 값으로 채움.
- **TC:** 정상: 108칸 이하 줄은 그대로. 경계: 딱 108칸·넓은 글자·공백 우선 접기, 글자 손실 없음.
- **개발:** `termux/run_all.py`, `termux/tools/anon.py`(신규), `termux/deck/sections/`(7개), `termux/deck/claims.md`, `termux/out/native_device.txt`, `index.html`, `README.md` 외
- **검증:** 단위 테스트 전부 통과 · make all 오류 0건 · 602장
- **비고:** 원본 data/device.txt 는 미커밋, 기기 식별값은 anon.py 로 가짜 처리. 팬텀 설정값은 앱에서 읽을 수 없어 미확인.

### [2026-09-19 02:35] mygit merge-base — 같은 날짜 공통 조상의 차례를 git 과 똑같이
- **기획:** 리뷰 2차에서 찾은 결함. git 2.55.0 commit-reach.c 의 paint_down_to_common 을 SPEC §10.2 에 옮김.
- **TC:** golden 에 criss-equal(같은 날짜 교차 머지) 추가, 인자 순서 뒤집기 — 다섯 언어 모두 빨강 확인.
- **개발:** `git/{py,go,ts,java,cpp}` 의 walk 5개, `git/tools/make_golden.py`, `git/SPEC.md`, `git/deck/sections/19_mygit.html`
- **검증:** py 137·ts 134·java 135·go·cpp 85 통과 · 대조표 60칸 ok · record 1,240개 3회 동일
- **비고:** 기존 대본·장면의 출력은 그대로(날짜가 모두 달랐음). 덱 1,830장.

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

---
## Archive
- [2026-09](history/archive/history-2026-09.md) — 104 entries
