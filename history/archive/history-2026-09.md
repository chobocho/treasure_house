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

### [2026-09-07 04:22] 보리차 덱 리뷰 — 사실오류 5건·표기 4건·상호참조 5건·중복 제목 10건 정정
- **기획:** 완성된 502장을 처음부터 훑어 숫자·사실·상호참조를 소스와 대조. 손으로 쓴 예시 코드가 생기면서 표지의 약속이 더는 참이 아니게 된 것을 바로잡음.
- **TC:** 덱이 언급한 시험 이름 전수 존재 확인, make 타깃 전수 확인, U+FFFD 검사, 중복 슬라이드 제목 검사, go list -deps 로 2부 의존 표 대조. 예시 시험 둘을 실제 파일로 만들어 시험 3종 추가.
- **개발:** deck/sections/{00,01,02,03,06,12,13}.html, deck/claims.md, tea/example_test.go, style/join.go·apps/{bugs,monitor}·examples/{01_hello,03_keys} 주석, index.html·README.md 숫자
- **검증:** make deck 502장 오류 0건 커버리지 12350/12350, deck-check 전 항목 통과, embed_mono_font --check 통과, go test 전 패키지 통과
- **비고:** 기능키 번호(14는 F4·16이 빈 자리), 간접 의존 15개, D2Coding 저작권 NHN, 시험 비율 3분의 1 — 전부 실물 대조로 정정.

### [2026-09-07 04:12] 보리차 덱 완성 — 8~14부 집필과 카드 등록 (501장)
- **기획:** 8부 style(34장)·9부 widgets(44장)·10부 testkit(27장)·11부 응용(26장)·12부 대조(16장)·13부 마무리(21장)·부록. 12부에 실을 실제 성능 수치를 위해 벤치마크 네 벌을 추가하고 make bench 로 out/bench.txt 를 남김.
- **TC:** 벤치 20종(폭·렌더·파서·스타일), 전 패키지 시험 유지. 조립마다 커버리지 12280/12280·오류 0건, check_deck.js 전 항목 통과, embed_mono_font.py --check 통과.
- **개발:** deck/sections/{08..13,14b}.html, {width,render,input,style}/bench_test.go, Makefile bench, out/{bench,binsize}.txt, index.html 카드, README.md 행
- **검증:** make deck 501장 오류 0건 · 1344KB, 기록 7종·터미널 캡처 19개 재생 정상
- **비고:** 한 프레임(한 줄 변경) 76us — 60fps 예산 16,666us 의 0.5퍼센트. 스타일 값 복사 130ns·할당 0. 숫자로 말할 수 있게 됨.

### [2026-09-07 03:47] 보리차 덱 본문 — 4~7부 집필 (350장)
- **기획:** 4부 term(28장·플랫폼 갈래와 정리 순서), 5부 input(44장·모든 바이트 경계 계약), 6부 render(24장·바이트 골든), 7부 width(23장·모호 폭 결정과 글꼴 이야기).
- **TC:** 조립마다 커버리지 전 줄·오류 0건. 6부는 tmux wrap before/after 캡처, 7부는 width_bad/ok 재생 기록을 슬라이드에 실어 함정을 눈으로 보이게 함.
- **개발:** deck/sections/{04_term,05_input,06_render,07_width}.html
- **검증:** make deck 350장 오류 0건, make deck-check 전 항목 통과
- **비고:** 덱이 싣는 D2Coding 이 ①②③ 을 두 칸으로 그리는 것을 7부에서 그대로 다룸 — 빌더 경고가 슬라이드의 근거가 된다.

### [2026-09-07 03:37] 보리차 덱 본문 — 0~3부 집필 (265장)
- **기획:** 0부(완성품·약속), 1부(터미널의 실체 27장), 2부(설계 15장), 3부(tea 핵심 루프 46장). 코드는 전부 실제 파일에서 잘라 오고, 화면은 tmux 캡처를 그대로 싣는다.
- **TC:** 조립할 때마다 커버리지 전 줄·오류 0건 확인. 인라인 SVG 도해 4종을 rsvg-convert 로 PNG 렌더해 눈으로 확인(Elm 순환도 라벨 겹침 1건 수정).
- **개발:** deck/sections/{00_start,01_terminal,02_design,03_tea}.html, deck/claims.md(주장 20건과 출처)
- **검증:** make deck 265장 오류 0건, make deck-check 전 항목 통과
- **비고:** VT100 1978·ANSI X3.64 1981·DEC 모드들·UAX #11·Bubble Tea v0.7.0(2020-05-26) 등 사실 주장은 전부 웹으로 확인해 claims.md 에 출처를 남김.

### [2026-09-07 03:18] 보리차 10단계 — 덱 빌드 체계 이식과 뼈대
- **기획:** tetris_tui/deck 도구 일습을 boricha/deck 으로 복사하고 제목·브랜드·출력 경로·기록 목록·커버리지 대상만 교체. 15개 부의 sections.json 과 스텁을 만들어 파이프라인 전체를 먼저 통과시킴.
- **TC:** 첫 조립에서 커버리지 12078/12078·오류 0건, check_deck.js 전 항목 통과(기록 7종 마운트·재생, DeckMono woff2 내장, 고정폭 목록 7곳 전부 우선).
- **개발:** deck/{build_deck,gen_appendix,gen_fonts,hl,chunks,split_ranges,test_fonts,untab}.py, player.js, check_deck.js, extra.css, base/, sections/ 스텁 15개
- **검증:** make deck → 181장 1006KB, make deck-check 오류 0건
- **비고:** 글꼴 폭 계약을 모호(A) 글자에 한해 경고로 완화. D2Coding 이 ①②③ 을 두 칸으로 그리는 것은 글꼴 잘못이 아니라 그 글자의 성질이다 — 칸이 맞아야 하는 캡처에는 쓰지 않는다.

### [2026-09-07 03:11] 보리차 9단계 — 캡스톤 셋: 할 일·시스템 모니터·전시장
- **기획:** 지금까지 쌓은 층을 전부 쓰는 응용 셋. 파일 입출력·주기적 표본 수집·화면 나누기를 각각 맡는다. 모델은 apps/ 라이브러리에 두고 cmd/ 는 얇게 — tools/record 가 import 해야 하기 때문(package main 은 import 불가).
- **TC:** todo 12종(추가·빈 값 거부·취소·완료·삭제·같은 글 중복·거른 상태 삭제·거르는 중 타이핑·저장/불러오기·없는 파일·배치 비활성·화면 크기), monitor 6종(CPU 차분 6경우·메모리·실제 /proc·스파크라인 6종과 폭 불변·멈춤/재개·화면 크기), showcase 5종(탭 순환·키 기록·모든 탭 크기·눈금 정렬과 길이·마우스).
- **개발:** apps/{todo,monitor,showcase}, cmd/{todo,monitor,showcase}, tools/record 등록부, Makefile 앱 캡처 규칙
- **검증:** go test 전 패키지 통과, make record 두 번 md5 동일, tmux 76×22 실캡처 3종, 누적 12,074줄
- **비고:** 거른 목록에서 값으로 지우면 글이 같은 항목 중 앞의 것이 지워진다 — 자리 번호를 항목에 붙여 해결.

### [2026-09-07 02:59] 보리차 8단계 — testkit·record·ansi2html과 함정 시연
- **기획:** 덱의 모든 화면을 실제 실행에서 뽑기 위한 장치. 진짜 Program 은 고루틴과 시계 위에 있어 결정론이 안 되므로, 같은 규칙을 시계 없이 다시 쓴 testkit 을 만들고 진짜 Program 과 대조하는 시험으로 지켜본다. 각본은 진짜 터미널 바이트로 바뀌어 진짜 파서를 지난다.
- **TC:** 각본 문법 10종·오류 5종·걸음→바이트 16종, 프레임 모양 불변, 프레임 수·이름표 짝, **두 번 돌려 프레임 동일(결정론)**, 기다리기가 명령을 돌림, q 조기 종료, 색 수준 지정, **진짜 Program 과 최종 모델 일치**, tea.Expand.
- **개발:** testkit/{script,testkit}.go, tools/{record,ansi2html}, apps/bugs, cmd/bugs, tea/cmd.go(Expand), Makefile record/html/logs
- **검증:** go test 전 패키지 통과, make record 두 번 md5 동일, tmux before/after 캡처 2종, 누적 10,556줄
- **비고:** 줄 넘침 함정은 우리 tea 로는 재현 불가 — 렌더러가 이미 자른다. 그래서 프레임워크를 거치지 않는 판으로 시연한다.

### [2026-09-07 02:45] 보리차 7단계 — widgets 부품 일곱 종
- **기획:** Bubbles 부분집합. 부품도 앱과 같은 모양(값 모델·Update·View)이되 Update 가 자기 타입을 돌려줘 부모가 그대로 대입한다. 키 배치와 도움말 문구를 한 값(Binding)에 묶어 둘이 어긋날 자리를 없앰.
- **TC:** Binding 일치·비활성·값 독립, 도움말 짧은/펼친 형태와 폭 제한, 스피너 회전·되감기·중복 울림 차단·그림 폭 일치, 진행 막대 경계(NaN·음수·초과·좁은 폭), 입력창 한글 룬 단위·커서·ctrl+u/w·글자수 제한·붙여넣기·초점·가로 스크롤·폭 불변, 목록 커서/스크롤/거르기(대소문자·커서 되돌림·거르는 중 j 입력), 뷰포트 모양 불변·클램프·휠·키 배치 일치.
- **개발:** widgets/{keymap,help,spinner,progress,textinput,list,viewport}.go, examples/10_widgets
- **검증:** go test 전 패키지 통과, go vet 무경고, 교차 컴파일 유지, tmux 실캡처(부품 6종 한 화면·한글 열 정렬·거르기 3/6), 누적 8,733줄
- **비고:** 거르는 중에는 모든 키가 입력창으로 가야 한다 — 안 그러면 "java" 를 칠 수 없다.

### [2026-09-07 02:32] 보리차 6단계 — tea 핵심 루프와 예제 사다리 01~09
- **기획:** Elm 아키텍처. 모델은 값, Update 는 고친 복사본과 Cmd 를 돌려준다. 고루틴 셋(입력·명령·주 루프)과 채널 하나. 루프 자체는 30줄이고 나머지 코드는 그 30줄을 짧게 유지하려고 있다.
- **TC:** 루프 갱신·EOF 종료·시작 사건(크기·색 수준), Init Cmd, Batch 동시성(느린 것 먼저 넣어도 빠른 것 먼저 도착), Sequence 순서, nil Cmd 무시, Tick/Every 1회성과 재예약 패턴, 밖에서 Send, 렌더러 유무, 종료 정리, 패닉 뒤 터미널 복구, 복사본 안 돌려주면 변경 사라짐.
- **개발:** tea/{msg,key,model,cmd,options,program}.go, examples/01~09, Makefile tmux-smoke 재작성
- **검증:** go test 전 패키지 통과, go vet 무경고, 교차 컴파일 유지, tmux 80×24 실캡처 10종(마우스 SGR·붙여넣기 한 덩어리·키 이름 확인), 누적 6,716줄
- **비고:** 마우스·붙여넣기는 tmux send-keys -H 로 실제 바이트를 밀어 넣어 증명함.

### [2026-09-07 02:19] 보리차 5단계 — render 줄 단위 diff 렌더러
- **기획:** 매 프레임 전체를 다시 그리면 깜빡인다. View 문자열을 화면 크기로 자른 Frame 으로 만들고, 지난 프레임과 줄 단위로 비교해 달라진 줄만 고쳐 쓴다. Write/Flush 를 나눠 초당 fps 번으로 제한.
- **TC:** Frame 자르기 7종(폭·높이·한글·꾸밈), Diff 7종(늘고 줄고 사라짐), 렌더러 바이트 골든 9종(첫 그리기·무변화 무출력·줄 축소 잔상 지우기·Repaint·Resize·Clear·동기화출력·오버플로), 줄 끝 공백 제거 7종과 diff 오염 방지, 시계 Start/Stop.
- **개발:** render/{buffer,diff,renderer,cursor}.go + 테스트 4개
- **검증:** go test 전 패키지 통과, go vet 무경고, 교차 컴파일 유지, 누적 4,977줄
- **비고:** 줄 끝 공백은 \e[K 덕에 뗄 수 있지만 배경색이 걸린 줄은 예외 — 그 공백이 색칠된 칸이다.

### [2026-09-07 02:13] 보리차 4단계 — style 꾸미기 층(Lip Gloss 부분집합)
- **기획:** 값 의미론 스타일. 색 프로필(없음/16/256/24비트) 판별과 내림 맞춤, 패딩·여백·정렬·테두리를 8단계 파이프라인으로 고정. 폭 계산은 전부 width 패키지 경유.
- **TC:** SGR 합성 9종, 값 복사 독립성, 패딩 CSS 4규칙, 폭·정렬·높이, 테두리 5종과 변 고르기, 파이프라인 순서(배경은 패딩까지만), 테두리 색, "모든 줄 폭 동일" 불변식, Join/Place 15종, 색 시퀀스 20종·프로필 판별 12종.
- **개발:** style/{color,palette,border,style,render,join}.go + 테스트 3개
- **검증:** go test 전 패키지 통과, go vet 무경고, 교차 컴파일 유지, 누적 4,319줄
- **비고:** 24비트→16색 내림에서 RGB 거리는 분홍을 은색으로 고른다. redmean 가중식으로 교체(49645 대 48900) — 덱의 비교 슬라이드 재료.

### [2026-09-07 02:05] 보리차 3단계 — width 글자 폭 표(한글 두 칸 문제)
- **기획:** 터미널은 글자를 칸으로 센다. 한글·한자·이모지는 두 칸. Go 표준 라이브러리에 답이 없어 유니코드 East_Asian_Width 표를 직접 실어 이분 탐색한다. 네트워크가 없어 자료는 python unicodedata(16.0.0)에서 뽑아 형식과 출처를 파일 머리에 명시.
- **TC:** RuneWidth 23종(한글·전각·이모지·결합문자·한글자모·제어), StringWidth ANSI 무시, Truncate 경계(반 칸 불가·꾸밈 보존·0/음수), Pad, Wrap 낱말·강제분할·줄바꿈 보존, 폭 2~20 전수로 "어느 줄도 폭 초과 없음" 불변식.
- **개발:** width/{widthdata.txt,table.go(생성),width.go,truncate.go}, tools/gen_width/main.go, Makefile gen-width
- **검증:** go test 전 패키지 통과, go vet 무경고, 생성기 두 번 돌려 md5 동일(결정론)
- **비고:** 모호(A) 부류는 1칸으로 결정 — 박스 문자가 여기 속해 2칸으로 보면 상자가 두 배가 된다.

### [2026-09-07 01:59] 보리차 2단계 — input 입력 파서(바이트 → 사건)
- **기획:** 터미널 입력은 바이트로만 온다. CSI/SS3 문법을 상태 기계로 옮겨 키·마우스·붙여넣기·포커스로 바꾸는 층. tea 가 input 을 쓰는 방향이라 순환을 피해 input 을 먼저 만듦(PLAN §8 순서 변경, 로그에 기록).
- **TC:** 바이트→사건 대응표 70여 건(한글·이모지·조합키·SGR 마우스·붙여넣기), 같은 입력을 **모든 바이트 경계에서 잘라** 결과 동일 검증, 한 바이트씩 흘려넣기, 반쪽 UTF-8 대기·깨진 UTF-8 폐기, ESC 단독→Flush, 붙여넣기 중 Flush 무시, Reader 시계 4종.
- **개발:** input/{keys,decoder,mouse,paste,reader}.go + 테스트 3개
- **검증:** go test 통과(input·term), go vet 무경고, 교차 컴파일 유지, 누적 2,302줄
- **비고:** android/arm64 는 -race 미지원 — 경합 검증은 설계와 타이밍 테스트로 대신함.

### [2026-09-07 01:47] 보리차 1단계 — 모듈·Makefile·term 드라이버·날것 터미널 예제
- **기획:** boricha/PLAN.md의 §8 커밋 1. Bubble Tea 같은 TUI 프레임워크를 표준 라이브러리만으로 바닥부터. 첫 층은 터미널 드라이버와 "프레임워크 없이 해 보기" 데모.
- **TC:** 시퀀스 바이트 대조 21종, CursorTo/Up/Down/ToCol 경계값(0·음수), Cleanup 역순·멱등·켠 것만 되돌리기, MakeRaw 비트 산술(가짜 Termios 전비트 1), 무관 필드 보존, winsize 0×0 거부, 비터미널 오류.
- **개발:** boricha/go.mod, Makefile, term/{seq,term,term_unix,term_windows,termios_unix,termios_linux,termios_darwin}.go, examples/00_raw/main.go 외 3개 파일
- **검증:** go test 통과(term ok), go vet 무경고, GOOS=darwin/windows 교차 컴파일 성공, tmux 80×24 실캡처 out/tmux_00_raw.txt(방향키 = 1B 5B 44)
- **비고:** macOS termios 경로는 컴파일만 확인, 실행 미검증. 덱 조립은 §8 커밋 10부터.

### [2026-09-07 10:06] template.html 고정폭 글꼴(DeckMono) 내장과 tools/embed_mono_font.py
- **기획:** template 계열 덱이 Consolas·SF Mono를 앞세워 한글·박스 문자가 다른 글꼴로 빠지며 아스키 표가 깨짐. Bubble Tea 덱에서 검증한 D2Coding 서브셋 내장을 공용 스크립트로 일반화.
- **TC:** 고정폭 요소 글자 수집·엔티티 복원, ASCII·박스 항상 포함, 반각 500/전각 1000 폭 계약과 위반 감지, 이모지 경고, 삽입·제자리 교체·두 번 돌려도 동일·저장 시각 미기록·CRLF 보존·style 없음, check 4종 (19건).
- **개발:** tools/embed_mono_font.py, tools/test_embed_mono_font.py, template.html(고정폭 목록 17곳 통일·글꼴 21KB·글꼴 슬라이드 1장·사용법·점검·함정표), CLAUDE.md
- **검증:** 19 passed, 0 failed · template.html --check 통과 · Go_Bubble_Tea 덱 --check 통과 · 태그 균형 확인
- **비고:** 기존 template 계열 문서 20개는 후속 작업으로 같은 스크립트를 일괄 적용 예정. Playwright를 못 쓰는 환경이라 브라우저 렌더링은 눈으로 확인하지 못함.

### [2026-09-07 05:17] 보리차 덱 2차 리뷰 — 사실오류 26건·모순 6건·표기 4건·코드 절단 11파일 재정렬·테마를 보리차 배색으로
- **기획:** 502장을 두 몫으로 나눠 전수 재검토(서브에이전트 2개). 소스가 자란 뒤 슬라이드의 코드 절단 범위가 함수 경계에서 밀려 캡션과 다른 코드를 보이던 것을 발견해 11개 소스 파일을 다시 잘랐다. 테트리스 덱에서 물려받은 남색·청록 배색을 보리차(볶은 갈색·호박색·크림)로 교체.
- **TC:** 절단 범위가 1..N 을 빈틈·중복 없이 덮고 45줄 이하인지 스크립트로 검증, 벤치 숫자를 out/bench.txt 와 대조, 모듈 캐시(bubbletea·ultraviolet·lipgloss·bubbles·go-runewidth)로 남의 소프트웨어 주장 대조, 배색 대비율 계산(본문 15.5:1, 보조 8.9:1).
- **개발:** deck/base/{deck_head,deck_tail_scripts}.html, deck/extra.css, deck/sections/{01..14b}.html, deck/claims.md(#23~26 추가), tea/program.go·style/style.go·width/width.go·examples/05_window 주석, index.html·README.md(503장) 외 3개 파일
- **검증:** make deck 503장 오류 0건 커버리지 12350/12350, deck-check 전 항목 통과, embed_mono_font --check 통과, go vet 통과, go test 8패키지 ok
- **비고:** Bubble Tea v2 사건 큐는 무제한이 아니라 버퍼 없는 채널, Key.String() 은 공백도 "space"(우리와 같음), ▁▂▃ 블록은 N 이 아니라 A(모호), Style 은 100이 아니라 300바이트, 렌더 벤치 76→86us — 전부 실물 대조로 정정. 부록에 "주장과 근거 ③" 한 장이 늘어 503장.
### [2026-09-07 05:51] 보리차 덱 14장 키 배치표 — 펼친 폴더블(~768px)에서 옆 칸을 덮어쓰던 것 정정
- **기획:** `.keys` 격자의 칸 최소폭 9rem 은 테트리스 덱의 "← →" 용이었다. 보리차엔 "go run ./examples/01_hello" 같은 긴 nowrap 명령이 들어와 4칸으로 쪼개지는 768px 부근에서 넘쳤다.
- **TC:** 폭별 칸 수 계산(374px 1칸·768px 2칸·1120px 3칸)과 가장 긴 명령+설명 폭 대조. `make deck` 오류 0건·`make deck-check`·글꼴 `--check` 통과.
- **개발:** boricha/deck/extra.css(최소폭 18rem, `.keyrow>b` 자식 선택자, span min-width:0), boricha/deck/sections/00_start.html(13장 로그를 끝 13줄로), 나만의_Bubble_Tea_만들기.html 재조립
- **검증:** make deck 오류 0건, make deck-check 오류 0건, embed_mono_font --check 통과
- **비고:** 13장 "make deck 의 끝부분"이 커밋본에선 0줄(빌드 중 로그가 비어 있던 시점에 읽힘)이었던 것을 함께 바로잡았다. 실기기 확인은 못 했으니 폴드8에서 재확인 필요.

### [2026-09-08 06:49] Keycloak×AD 연동 덱 — Opus 빌드 세션용 작업 계획 작성
- **기획:** k8s 서비스에 Keycloak으로 AD 로그인을 붙이는 과정을 웹 개념이 없는 대학 4학년 눈높이로 설명하는 덱(≈800장, 상한 1000)의 에이전트용 플랜. 12부 구성·증거 등급(실행/구문/문서)·fakead·miniidp 미니어처 설계·커밋 14단계.
- **TC:** 해당 없음(계획 문서). 이 기기 도구 현황(docker·kubectl 없음, Java21·Go1.27 있음, RAM 여유 2.2GB)을 확인해 §3에 고정.
- **개발:** keycloak_ad/PLAN.md
- **검증:** UTF-8 확인, §10 결정 7건 사용자 기본값 확정 반영
- **비고:** 실제 덱·소스는 Opus 세션이 PLAN.md 순서대로 진행. Keycloak 실행은 메모리 게이트(≥1.8GB) 통과 시에만.

### [2026-09-08 07:10] Keycloak×AD 덱 뼈대 — 빌더·표지 12장·부 표지 12장
- **기획:** PLAN.md §8 1단계. 덱 조립 도구 일습과 0부(표지·전체 그림·세 세션·근거 등급·등장인물)를 세우고, 1~12부는 표지만 두어 처음부터 열리는 상태를 만든다.
- **TC:** `deck/check_deck.js` 를 먼저 써서 RED(덱 없음) 확인 → 구조·상호참조·자기완결성 8종 검사. `certs/check_certs.sh` 도 RED(인증서 없음) → 체인·SAN·EKU·키 짝 검사.
- **개발:** keycloak_ad/{go.mod,Makefile,.gitignore}, deck/{build_deck,verify_deck,chunks,gen_system}.py, deck/check_deck.js, deck/base/{head,tail}.html, deck/sections/ 13개, deck/figs/ 13개, certs/{make,check}_certs.sh, deck/claims.md
- **검증:** make all SKEL=1 — 조립 오류 0건 · 역검증 통과 · deck-check 오류 0건 · 글꼴 --check 통과. 24장 171 KB. 인증서 검사 오류 0건.
- **비고:** PLAN.md §5 는 boricha 도구 재사용을 지시했으나, boricha 계열은 `<section class="slide">` 구조라 template.html 의 `__demo`·`.quiz`·`#ch` 상호참조와 맞지 않는다. 저장소 다수(덱 20여 개)가 쓰는 template 계열 = rts/deck 조립기 계보로 바꿨다. index·README 카드는 PLAN §8 13단계(공개)에서 함께 넣는다.

### [2026-09-08 08:40] Keycloak×AD 덱 1부 — 웹이 돌아가는 법 104장, 서버 4종·캡처 38개
- **기획:** PLAN.md §8 2단계. 웹을 처음 만지는 사람 기준으로 HTTP·상태코드·리다이렉트·폼·쿠키·TLS·도구상자를 한 장에 한 개념씩. 코드는 전부 실행되는 실물, 출력은 전부 진짜 캡처.
- **TC:** 02·03·04 는 뼈대만 두고 RED 확인 후 GREEN(총 40개 테스트). 01 은 구현이 먼저라 정렬·Host·404 를 일부러 깨뜨려 시험이 무는지 확인. TLS 는 진짜 악수 3종(우리 CA 신뢰/불신/이름 불일치).
- **개발:** web/01_hello · 02_form_cookie · 03_redirect · 04_tls (+테스트), tools/{record.sh,scrub.py,width.py,rewrap.py}, deck/{demos.js,budget.txt,pending.txt}, deck/sections/01_web.html 외 3개 파일
- **검증:** go test 4패키지 통과 · vet 통과 · make record 3회 md5 동일(38개) · 조립 오류 0건 · 역검증 통과(코드 33·출력 44 전부 일치) · deck-check 0건 · 글꼴 --check 통과. 덱 127장 315 KB.
- **비고:** scrub 이 sha256 출력까지 가짜로 바꾸던 것을 잡아 '자리로 고르는' 방식으로 고쳤다. go run 유령 프로세스가 옛 코드의 출력을 캡처하던 것도 잡아 빌드 후 실행+포트 선점 검사로 바꿨다. 1부가 목표 80장 대비 104장 — 예상 합계 882장(상한 1000)이라 아직 여유 있다.

### [2026-09-08 09:20] LDAP 코어 — BER·프로토콜·가짜 AD·ldapcli, 캡처 14개
- **기획:** PLAN.md §8 3단계 앞부분. Keycloak 이 AD 에게 실제로 묻는 것만 골라 흉내 내는 LDAP 서버와, 오간 바이트를 풀어 보여 주는 클라이언트. 표준 라이브러리만 씀.
- **TC:** 네 묶음 모두 뼈대→RED→GREEN. BER 는 골든 바이트(익명 바인드 14바이트·정수/길이 표), 필터는 글↔나무↔바이트 3방향 왕복, 서버는 진짜 소켓으로 종단 시험(쪼개 보내기·LDAPS 악수·잠금).
- **개발:** ldap/ber ldap/proto ldap/fakead(dir·server·main) ldap/ldapcli(dump·main), data/campus.ldif(15항목), tools/record.sh 3부 캡처
- **검증:** go test 8패키지 통과 · vet 통과 · make record 2회 md5 동일(52개) · 조립 오류 0건 · 역검증 통과 · deck-check 0건 · 글꼴 통과
- **비고:** 덱 본문(3부)은 다음 커밋. 소스 2,300줄이 deck/pending.txt 에 대기 중. AD 진단 코드(52e·533·775·525)와 memberOf 계산·objectGUID 16바이트 이진값을 그대로 재현했다.

### [2026-09-08 10:42] 3부 본문 — 회사 계정의 세계 83장, 전체 소스 부록 100장
- **기획:** PLAN.md §8 3단계 뒷부분. 디렉터리·DN·AD 속성·그룹/memberOf·BER 바이트·바인드·검색·LDAPS·서비스 계정·안 하는 것·마무리 9개 장. 소스 전문은 새 부록 절이 싣는다.
- **TC:** 로그 폭 시험을 새로 써서 RED 확인 → Server.Close 가 유휴 연결 때문에 안 꺼지던 결함을 잡아 연결 추적을 넣었다. 진단 문구 접기(wrapCells)도 RED→GREEN.
- **개발:** deck/sections/{03_ad,13_appendix}.html, deck/figs/ad_tree.svg, deck/demos.js(ldap-filter·ldap-dn), ldap/fakead/server.go, ldap/ldapcli/dump.go, deck/{order,budget,pending}.txt, Makefile
- **검증:** 덱 309장 572 KB · 소스 커버리지 3833/3833줄 100퍼센트 · 조립 오류 0건 · 역검증 통과(코드 159·출력 62) · deck-check 0건 · 글꼴 통과 · make record 2회 md5 동일(52개) · test 8패키지 · vet 통과
- **비고:** 3부 83장(목표 75). 부록은 §7 에 없던 절이라 13번으로 새로 뒀다 — 커버리지 약속(§2.1)을 지키면서 교육 장을 안 부풀리는 자리. 예상 합계 989장(상한 2000).

### [2026-09-08 11:25] OIDC 기초 — JWT·PKCE, LDAP 클라이언트 분리
- **기획:** PLAN.md §8 5단계의 앞부분. 토큰을 만들고 확인하는 층(jwt)과 가로챈 코드를 못 쓰게 만드는 층(pkce). miniidp 가 AD 에 물어보려면 LDAP 클라이언트가 라이브러리여야 해서 ldapcli 에서 뽑아냈다.
- **TC:** 셋 다 뼈대→RED→GREEN. jwt 는 RFC 7515 A.1·RFC 7519 §3.1 골든 벡터와 공격 넷(alg=none·alg 혼동·내용 변조·남의 열쇠), pkce 는 RFC 7636 부록 B 벡터. client 는 진짜 가짜 AD 를 띄워 놓고 시험한다.
- **개발:** oidc/jwt oidc/pkce, ldap/client(신규), ldap/fakead 를 라이브러리+cmd 로 분리, ldapcli 를 client 위로, tools/record.sh(본문 전용 캡처)
- **검증:** test 12패키지 · vet 통과 · make record 3회 md5 동일(54개) · 조립 오류 0건 · 역검증 통과 · deck-check 0건 · 글꼴 통과 · width 18파일 통과
- **비고:** TLS 1.3 세션 티켓이 악수 뒤에 비동기로 와서 -v 캡처의 줄 번호가 가끔 밀렸다. 본문만 따로 뜨는 캡처를 더해 인용을 그쪽으로 옮겼다. miniidp·miniapp·jwtool 과 4부 본문은 다음 커밋.

### [2026-09-08 13:55] OIDC 전 과정 실물 — miniapp·jwtool, 캡처 32개
- **기획:** PLAN.md §8 5단계의 가운데. 앱(RP) 쪽과 토큰을 눈으로 보는 도구. miniapp 시험이 진짜 IdP를 상대하도록 miniidp를 라이브러리+cmd로 갈랐다(fakead와 같은 방식).
- **TC:** 뼈대→RED→GREEN. miniapp은 진짜 miniidp를 띄워 브라우저처럼 따라가는 통합 시험(로그인·403·state 재사용·nonce 바꿔치기·남의 열쇠·로그아웃). jwtool은 alg=none·변조·기한·대상·발급자. 새 시험 4종은 변이를 넣어 실제로 무는지 확인했다.
- **개발:** oidc/miniapp, oidc/jwtool, oidc/miniidp(분리), tools/tamper_jwt.py, tools/record.sh 7절, tools/scrub.py, ldap/fakead/server.go, deck/sections/01_web.html 외 3개 파일
- **검증:** test 14패키지 · vet·gofmt·72칸 폭 통과 · make record 3회 md5 동일(88개) · 조립 오류 0건 · 역검증 307장 통과 · deck-check 0건 · 글꼴 통과
- **비고:** 캡처하다 결함 4건을 찾아 고쳤다 — 로그아웃이 콜백으로 돌아가 400(PostLogoutURIs 분리), 가짜 AD의 SEARCH 로그 143칸(접어 적기), go test 캐시로 캡처가 두 판(-count=1), 토큰의 iat·jti로 재현 불가(FixForCapture). 4부 본문은 다음 커밋.

### [2026-09-08 15:40] Keycloak×AD 덱 4부 본문 — 116장, 커버리지 100%
- **기획:** PLAN §8 5단계의 마지막. 9개 장(위임의 이유·인가 코드 흐름·state/nonce/PKCE·토큰 세 장·JWT 해부·JWKS와 안내문·앱 쪽·세 세션과 로그아웃·직접 돌려 보기), 퀴즈 8, 데모 2.
- **TC:** 본문 커밋이라 새 시험은 없다. 조립기의 검사(폭·장수·근거 배지·커버리지)와 역검증·deck-check·글꼴검사가 관문이다.
- **개발:** deck/sections/04_sso.html(신규), 13_appendix.html(FULLSRC 11개), deck/demos.js(+2), deck/claims.md(4부 28행), deck/pending.txt(비움), tools/showurl.py(신규), tools/record.sh, tools/scrub.py 외 1개 파일
- **검증:** 504장 · 커버리지 6465/6465줄 100% · 조립 0건 · 역검증 통과(코드 274·출력 99) · deck-check 0건(퀴즈 24·데모 11) · 글꼴 통과 · make record 3회 md5 동일(94개) · test 14패키지
- **비고:** 200칸 넘는 주소를 실을 수 없어 tools/showurl.py 로 칸마다 한 줄씩 펼쳤다. alg=none 사고의 연도를 적었다가 근거를 못 대 빼고 RFC 8725 로 대신했다. 0부와 4부의 세 세션 표가 어긋나 0부에 맞췄다.

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
