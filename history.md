### [2026-10-17 14:42] A2A 덱 7부 뒤 절반 — 파이썬 SDK 클라이언트·완성 에이전트·시험·SDK 고유 기능(59장)
- **기획:** 클라이언트, 숙소 에이전트 완성판, 프로세스 안 시험, v0.3 호환·DB 저장소·원격 측정을 설치본 소스와 실행 캡처로 보인다.
- **TC:** 정상 — 막는 호출·스트림, 되묻기 다중 턴과 골든 대조. 경계 — 모르는 응답 필드, 끝난 작업, 호환 스위치 끈 서버, extra 없는 DB 저장소.
- **개발:** a2a/deck/sections/07b_py.html, 07_py.html, 03_card.html, a2a/ex/py/07/, a2a/ex/run/07/, a2a/ex/*/agents/lodging.*
- **검증:** 낡은 캡처 23개 재실행 내용 일치, make all SKEL=1 rc=0 (679장, 어긋남 0건)
- **비고:** 7부 121장. 숙소 에이전트 셋에 region 표시를 달아 줄 번호 인용을 없앴다.

### [2026-10-16 17:43] A2A 덱 7부 앞 절반 — 파이썬 SDK 패키지·타입·실행기·처리기·서버(62장)
- **기획:** 파이썬 SDK 로 에이전트를 짓는 법을 설치본 소스에서 읽어, 8·9부가 따라 할 장 구조와 정리 표를 세운다.
- **TC:** 정상 — 단계 예제(메아리·견적)와 처리기 직접 호출. 경계 — 규칙을 어기는 실행기 일곱, 다른 id 의 Task, 아무것도 안 싣는 실행기, /a2a 에 단 JSON-RPC.
- **개발:** a2a/deck/sections/07_py.html, a2a/ex/py/07/, a2a/ex/run/07/, a2a/tools/check_width.py, a2a/tools/a2arun.py 외 다수
- **검증:** 도구 시험 145 통과, 07 캡처 --check 2~3회 일치, make all SKEL=1 rc=0
- **비고:** 예제 전 줄 72칸 검사를 lint 에 넣고 3~6부의 넘는 줄 17곳을 고쳤다.

### [2026-10-16 16:28] A2A 덱 6부 마지막 묶음 — 맨손 클라이언트·교차 매트릭스·놓친 것(39장)
- **기획:** 표준 라이브러리 클라이언트 셋을 만들고, SDK·맨손 서버 여섯 × 클라이언트 매트릭스로 상호운용을 확인하며, 맨손이 놓친 것을 증거와 함께 정리한다.
- **TC:** 정상 — ask 3 × 서버 6, 맨손 클라이언트 3 × 서버 6. 경계 — 문자열 historyLength, 숫자 id, 1.0.1·1.5 버전 헤더, 쿼리 버전, 반쯤 보낸 요청.
- **개발:** a2a/deck/sections/06c_bare.html, 06_bare.html, 06b_bare.html, a2a/ex/*/06/, a2a/ex/run/06/
- **검증:** 06 캡처 --check 2~3회 일치, make all SKEL=1 rc=0
- **비고:** 6부 131장. Go 맨손 서버의 입력 오류 무시를 고쳤다. TS SDK 는 1.0.1 을 거절해 §3.6 과 어긋난다.

### [2026-10-16 15:51] A2A 덱 6부 둘째 묶음 — 맨손 SendMessage·GetTask·CancelTask·SSE(45장)
- **기획:** 맨손 서버 셋의 작업 처리(이어 말하기·historyLength·취소)와 SSE 스트리밍(첫 이벤트 Task, 프레이밍, 닫기)을 와이어로 보인다.
- **TC:** 정상 — 다중 턴·스트림 ×3 서버. 경계 — 맥락 불일치, 끝난 작업, 재취소, 스트림 전 오류, 청크 경계에 걸친 한글 본문.
- **개발:** a2a/deck/sections/06b_bare.html, 06_bare.html, a2a/ex/py/06/, a2a/ex/ts/06/bare_lodging.ts, a2a/ex/run/06/
- **검증:** 06 캡처 --check 2~3회 일치, make all SKEL=1 rc=0
- **비고:** TS 맨손 서버가 청크 경계에서 한글을 깨던 결함을 고쳤다. 스트림 닫는 때가 §3.1.2 와 §11.7 에서 어긋난다.

### [2026-10-16 15:28] A2A 덱 6부 첫 묶음 — 맨손 서버 목표·디스패치·저장소(47장), 숙소 에이전트 결함 수정
- **기획:** 표준 라이브러리만으로 v1.0 숙소 에이전트를 세 언어로 만들고, 1~3장에서 목표·JSON-RPC 디스패치와 오류·Task 저장소와 전이를 보인다.
- **TC:** 정상 — ask 세 언어 × 맨손 서버 셋이 참조 대화록과 일치. 경계 — 잘못된 요청 10종, 버전 헤더 없음, 금지된 전이, 되물음 예시를 답으로 읽던 대화.
- **개발:** a2a/deck/sections/06_bare.html, 04_message.html, a2a/ex/*/06/, a2a/ex/run/06/, a2a/ex/{py,ts,go}/agents/lodging*
- **검증:** 04·06 캡처 --check 2회 일치, make all SKEL=1 rc=0
- **비고:** 완성 숙소 에이전트 셋이 자기가 되물은 말의 예시 날짜를 사용자 답으로 읽던 결함을 고쳤다.

### [2026-10-16 14:38] A2A 덱 5부 뒤 절반 — 종료 상태·historyLength·아티팩트·오류(57장), Go 이력 결함 수정
- **기획:** 거절·실패·취소, historyLength 세 경우, 아티팩트, 작업 둘레 오류와 ErrorInfo 모양을 세 서버로 보이고, 리뷰에서 드러난 Go 에이전트 이력 결함을 고친다.
- **TC:** 정상 — 세 언어 클라이언트로 GetTask·아티팩트 읽기. 경계 — 실행기 예외, 음수 historyLength, 재취소, 끝난 작업에 말 걸기, 같은 messageId 순서.
- **개발:** a2a/deck/sections/05b_task.html, 05_task.html, 04b_message.html, a2a/ex/go/agents/common/, a2a/ex/*/05/, a2a/tools/a2arun.py 외 다수
- **검증:** 03~05 캡처 --check 2~3회 일치, 도구 시험 141 통과, make all SKEL=1 rc=0
- **비고:** 5부 118장. Go Begin 이 되물은 말을 이력에서 지우던 것을 고치고 슬라이드 다섯 장을 바로잡았다.

### [2026-10-16 13:07] A2A 덱 5부 앞 절반 — Task 모양·상태 기계·막는 호출·다중 턴(61장)
- **기획:** Task 의 필드, 상태 아홉과 전이, blocking 과 returnImmediately, 완료 Task 읽기, INPUT_REQUIRED 다중 턴을 세 서버로 보인다.
- **TC:** 정상 — 숙소 세 번 되묻기 ×3 클라이언트, 교통 즉시 반환과 폴링. 경계 — 끝난 작업에 늦은 갱신, 거꾸로 가는 전이, 이어 말하기에 Task 다시 싣기.
- **개발:** a2a/deck/sections/05_task.html, 05b_task.html, a2a/ex/*/05/, a2a/ex/run/05/, a2a/deck/order.txt
- **검증:** 05 캡처 --check 3회 일치, make all SKEL=1 rc=0
- **비고:** 어느 SDK 도 전이를 막지 않는다. whats-new-v1 의 Task createdAt·lastModified 는 proto 에 없다.

### [2026-10-16 12:27] A2A 덱 4부 뒤 절반 — FilePart·contextId·멱등성·ProtoJSON(48장)
- **기획:** 파일 파트와 출력 모드, contextId 규칙(§3.4), 같은 messageId, ProtoJSON 입력 허용 범위를 세 서버에 실제로 던져 본다.
- **TC:** 정상 — menu.md 파일 파트, 맥락 규칙 여섯 탐침 ×3. 경계 — 100KB 넘는 본문, 지원 안 하는 미디어 타입, snake_case·소문자 enum·숫자 enum, 없는 status 필터.
- **개발:** a2a/deck/sections/04b_message.html, 04_message.html, a2a/ex/*/04/, a2a/ex/run/04/, a2a/tools/a2arun.py, a2a/deck/AUTHORING.md
- **검증:** 04 캡처 --check 2회 일치, 도구 시험 139 통과, make all SKEL=1 rc=0
- **비고:** 4부 102장. 파이썬 ListTasks 는 모르는 status 필터를 조용히 무시하고 전부 돌려준다.

### [2026-10-16 11:41] A2A 덱 4부 앞 절반 — Message·Part·응답 종류·DataPart(54장)
- **기획:** Message 필드, Part 네 가지와 kind 가 사라진 까닭, Message 응답과 Task 응답, DataPart 의 수를 세 언어 와이어로 보인다.
- **TC:** 정상 — 같은 파트를 세 SDK 로 만들어 와이어 비교, 수의 3×3. 경계 — 필수 필드 누락, v0.3 모양 파트, 내용 필드 둘, 없는 참조 작업.
- **개발:** a2a/deck/sections/04_message.html, 04b_message.html, a2a/ex/*/04/, a2a/ex/run/04/, a2a/deck/order.txt
- **검증:** 04 캡처 --check 2회 일치, make all SKEL=1 rc=0
- **비고:** TS 서버는 role·parts 가 없는 메시지도 받는다. Go 는 유효한 JSON 의 잘못된 파트에 -32700 을 낸다.

### [2026-10-16 10:57] A2A 덱 3부 뒤 절반 — skills·capabilities·캐싱·카드 검증기(51장)
- **기획:** 스킬 태그로 에이전트 고르기, 선언하지 않은 기능을 부를 때의 오류(§3.3.4), 카드 캐싱(§8.6), 카드 검증기를 세 언어로 보인다.
- **TC:** 정상 — 다섯 카드에서 태그로 고르기, 조건부 GET 3×3. 경계 — 기능 없는 에이전트에 스트림·푸시·확장 카드, 망가진 카드 셋, 패치 번호 판.
- **개발:** a2a/deck/sections/03b_card.html, 03_card.html, a2a/ex/*/03/, a2a/ex/run/03/, a2a/tools/a2arun.py
- **검증:** 03 캡처 --check 2회 일치, 도구 시험 138 통과, make all SKEL=1 rc=0
- **비고:** 3부 103장. 명세 옆 자료 디렉터리도 캡처 입력 해시에 넣었다.

### [2026-10-16 10:20] A2A 덱 3부 앞 절반 — Agent Card 1~4장(52장)과 와이어 탭 맵 정렬
- **기획:** 완성 에이전트 셋을 블랙박스로 띄워 카드의 필수 필드·well-known 경로·인터페이스 고르기·--url 과 프록시를 와이어로 읽는다.
- **TC:** 정상 — 세 언어 카드 비교, 문 둘 달린 카드에 세 클라이언트. 경계 — 옛 agent.json 404, 닿지 않는 --url, 경로 붙은 기준 주소, tenant.
- **개발:** a2a/deck/sections/03_card.html, 03b_card.html, a2a/ex/*/03/, a2a/ex/run/03/, a2a/tools/wiretap.py, a2a/deck/AUTHORING.md
- **검증:** 03 캡처 --check 3회 일치, 도구 시험 137 통과, make deck SKEL=1 오류 0
- **비고:** 파이썬 SDK 는 Struct·맵 키 순서를 프로세스마다 바꾼다 — 탭이 그 아래만 정렬한다(0부에 명시할 정규화).

### [2026-10-16 09:48] A2A 덱 2부 집필 — HTTP·JSON-RPC·SSE 바탕 지식(74장)
- **기획:** SDK 없이 세 언어 표준 라이브러리로 HTTP·JSON·JSON-RPC 2.0·SSE·비동기를 보여, 3부부터 A2A 와이어를 읽을 바탕을 깐다.
- **TC:** 정상 — 같은 일을 하는 3언어 예제 8벌, JSON-RPC 시험 본문 8종. 경계 — 30.0·2^53+1·null 대 빠짐, 빈 배치·id 없는 알림, CR 이 든 캡처.
- **개발:** a2a/deck/sections/02_basics.html, a2a/ex/{py,ts,go}/02/, a2a/ex/run/02/, a2a/tools/a2arun.py, a2a/data/sources.tsv 외 다수
- **검증:** 02 캡처 --check 2회 일치, 도구 시험 136 통과, make all SKEL=1 rc=0
- **비고:** 용어 "사건"→"이벤트". A2A 스펙은 배치를 말하지 않고 파이썬 SDK 는 배치를 거절한다.

### [2026-10-16 09:10] A2A 덱 에이전트 3언어 완성 — TS·Go 이식과 교차 검증
- **기획:** 파이썬 완성 에이전트 다섯과 ask·webhook 을 TS·Go 로 옮겨, 어느 언어 조합이든 같은 대화록이 나오게 한다.
- **TC:** 정상 — 참조 대화록 6종 × 언어 조합 8가지, 푸시 6쌍. 경계 — 되묻기 3회, 거절·예산 초과, 읽기 전용 토큰, 2차 취소, 401·토큰 오류.
- **개발:** a2a/ex/ts/agents/, a2a/ex/go/agents/, a2a/ex/py/agents/common.py, a2a/PLAN.md 외 다수
- **검증:** 조합별 대화록 일치(TS·Go 서버는 이어 말하기 뒤 task WORKING 한 줄), make all SKEL=1 rc=0
- **비고:** 파이썬 SDK 1.2.2 는 이어 말하기에 Task 를 다시 실으면 사용자 답을 버린다. Go 는 AUTH_REQUIRED 를 끝으로 보지 않아 실행기를 대기시켜 풀었다.

### [2026-10-16 07:46] A2A 덱 착수 — 뼈대·도구·시나리오 핵심
- **기획:** A2A v1.0.1 덱(상한 2000장)을 Py/TS/Go 3언어·워크숍 시나리오 하나로 만든다. 계획·시나리오 계약·목차·집필 지침을 쓰고 실행 도구부터 세운다.
- **TC:** 정상 — 골든 44건(손 계산) 세 언어 각각, 도구 시험 126개. 경계 — 정원 경계·연말 마감일·채식 초과·결재 기준 동액·빈 정산·문장 누락 항목.
- **개발:** a2a/PLAN.md, a2a/deck/{SCENARIO,OUTLINE,AUTHORING}.md, a2a/tools/a2arun.py·wiretap.py, a2a/deck/build_deck.py, a2a/ex/*/workshop/, a2a/ex/py/agents/ 외 다수
- **검증:** make all SKEL=1 rc=0 (44장·오류 0·어긋남 0), 골든 py/ts/go 44/44, 도구 시험 126 통과
- **비고:** 덱 HTML·index 카드는 본문이 찬 뒤에 커밋한다. 다음은 TS·Go 에이전트 이식과 2부부터 집필.

### [2026-10-13 12:39] Rust 덱 보강분·부록 리뷰와 전체 최종 점검 — 확장 완료(1,877장)
- **기획:** 1~16부에 끼운 27장이 뒤에서 배울 것을 미리 쓰지 않는지, 화면보다 넓게 말하지 않는지 보고, 부록의 새 표와 용어집 새 줄 48개를 정의한 슬라이드와 대조한 뒤 책 전체를 다시 돌린다.
- **TC:** 정상 — 책의 예제 1,329개 전수 재실행. 경계 — 싣지 않은 실행 8건 재탐침, 스레드 예제 둘 10회, 에디션 표의 예제 쌍 11개 비교.
- **개발:** rust/deck/sections/15_conc.html, 16_more.html, 06_own.html, 06b_own.html, 27_appendix.html 외 5개 조각, rust/deck/glossary.tsv, rust/deck/AUTHORING.md, rust/PLAN.md 외 2개 파일
- **검증:** make all rc=0 (1,877장·오류 0·어긋남 0), 전 예제 rsrun --check 1,329 일치·0 불일치
- **비고:** 근거없음 3·증거불일치 2·절단 1·표기 1·퀴즈 1건, 용어집 5줄 정정. 앞당겨 쓴 문법은 없었다. 17~26부 확장 끝, push 안 함.

### [2026-10-13 11:47] Rust 덱 앞 부 링크·낡은 문장 정리와 부록 갱신
- **기획:** 17~26부가 생기며 낡은 앞 부의 문장을 고치고 뒤 슬라이드로 가는 구절을 슬라이드당 하나까지 달며, 부록에 17~26부 찾아보기·용어집·에디션 표를 더한다.
- **TC:** 정상 — 낡은 문장 23곳, 앞으로 가는 링크 63곳, 용어 48개. 경계 — 건너뛴 쌍 113건 기록, 용어집 칸 수·중복 검사, 예제·캡처 무변경 확인.
- **개발:** rust/deck/sections/27_appendix.html 외 37개 조각, rust/deck/glossary.tsv, rust/deck/budget.txt, rust/data/features.tsv, index.html, README.md, rust/PLAN.md 외 2개 파일
- **검증:** make all rc=0 (1,877장·오류 0·어긋남 0·버전 표기 142건)
- **비고:** 부록 34→44장, 용어집 64→112낱말. 정의한 슬라이드가 없는 낱말(컬렉션 등)은 싣지 않았다.

### [2026-10-13 11:03] Rust 덱 1~16부 보강 — 27장, 예제 31개
- **기획:** 목차 계약의 보강분(1부 퀴즈 넷, 고친 쌍둥이, 증거 없던 문장의 증거)과 25·26부 리뷰가 드러낸 빈 곳(연산자 표, 공유 참조의 Copy, 값 없는 return, 블록 본문 클로저, Ord 의 슈퍼트레이트)을 새 슬라이드로 끼운다.
- **TC:** 정상 — 고친 쌍둥이와 실행 예제. 경계 — 컴파일 오류 9건·패닉 3건의 실제 메시지, 스레드 예제 둘 10회 반복.
- **개발:** rust/deck/sections/01_history.html, 03_types.html, 10b_trait.html, 16_more.html 외 13개 조각, rust/ex/03~16(31개), rust/out, index.html, README.md 외 3개 파일
- **검증:** make all rc=0 (1,867장·오류 0·어긋남 0·퀴즈 119), 바뀐 12개 디렉터리 rsrun --check 530 일치·0 불일치
- **비고:** 기존 예제·캡처는 무변경. 단형화 증거는 결정적인 캡처가 없어 싣지 않았다. 리뷰 전.

### [2026-10-13 10:06] Rust 덱 26부 뒤 절반(4~7장) 리뷰
- **기획:** 항목 28개를 캡처·고친 파일과 대조하고, 싣지 않은 실행 28건을 새로 돌리며, 배운 번호는 가르친 슬라이드가 보여 준 구간과 견준다.
- **TC:** 정상 — 싣지 않은 실행 28건 재실행(확인 28·어긋남 0). 경계 — 줄을 지운 탐침, 스레드가 든 고친 파일 둘 10회 반복.
- **개발:** rust/deck/sections/26b_errs.html, rust/deck/AUTHORING.md, rust/PLAN.md, history.md, Rust_기초_문법집.html
- **검증:** make all rc=0 (1,840장·오류 0·어긋남 0), rsrun --check ex/26 3회 108 일치·0 불일치
- **비고:** 표기 14·순서 12·증거불일치 6·근거없음 6·사실오류 2건. 예제와 캡처는 무변경. 26부 완료 — 17~26부 집필·리뷰가 모두 끝났다.

### [2026-10-13 09:21] Rust 덱 26부 앞 절반(1~3장) 리뷰
- **기획:** 항목 26개를 캡처·고친 파일과 나란히 놓고 읽는 법·처방·제목이 그 화면에 참인지 보고, 싣지 않은 실행을 모두 다시 돌린다.
- **TC:** 정상 — 싣지 않은 실행 21건 재실행(확인 21·어긋남 0·빠진 경고 1). 경계 — 줄을 하나씩 지운 탐침, 도움말과 쌍둥이의 글자 대조.
- **개발:** rust/deck/sections/26_errs.html, rust/deck/AUTHORING.md, rust/PLAN.md, history.md, Rust_기초_문법집.html
- **검증:** make all rc=0 (1,840장·오류 0·어긋남 0), rsrun --check ex/26 3회 108 일치·0 불일치
- **비고:** 사실오류 6·증거불일치 6·표기 6·근거없음 5·순서 2건. 예제와 캡처는 무변경. 넓게 말한 제목 넷을 그 화면만큼으로 좁혔다.

### [2026-10-13 08:49] Rust 덱 26부 컴파일 오류 처방전 — 뒤 절반(4~7장) 집필
- **기획:** 수명 6·트레이트 9·패턴 7·그 밖 6항목을 앞 절반과 같은 짜임(틀린 파일·읽는 법·처방·고친 쌍둥이)으로 한 장씩 쓴다.
- **TC:** 정상 — 고친 파일 28개가 경고 없이 돈다. 경계 — 후보 77개를 먼저 돌려 오류 하나로 나오는 것만 남기고, 도움말을 글자대로 적용한 실행을 따로 돌렸다.
- **개발:** rust/deck/sections/26b_errs.html, 26_errs.html, rust/deck/order.txt, rust/ex/26/*.rs(56개), rust/out/26/*.txt, index.html, README.md, rust/PLAN.md 외 2개 파일
- **검증:** make all rc=0 (1,840장·오류 0·어긋남 0·알림 0), rsrun --check ex/26 3회 108 일치·0 불일치
- **비고:** 새 오류 번호 15종(제목 기준 91종). 26부 70장으로 예산과 같다. 문법 오류 항목은 없다. 리뷰 전.

---
## Archive
- [2026-10](history/archive/history-2026-10.md) — 39 entries
- [2026-09](history/archive/history-2026-09.md) — 161 entries
