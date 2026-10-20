### [2026-10-18 22:42] A2A 덱 15부 셋째 조각 — 실패 경로(30장), 결재 반려 때 정산 작업 취소 수정
- **기획:** 숙소·식사 거절, 예산 초과, 결재 반려, 교통 취소를 세 언어 기획 에이전트로 돌려 어떻게 드러나는지 견주고, 반려 때 정산 작업이 AUTH_REQUIRED 로 남던 결함을 고친다.
- **TC:** 경계 — 2026-12-31·70명·채식 40명·예산 4,000,000원·"안 됩니다"·진행 중 교통 취소 ×3. 반려 시험 ×3(RED: CancelTask 없음).
- **개발:** a2a/deck/sections/15c_scenario.html, 15_scenario.html, 15b_scenario.html, 07_py.html 외 2개, a2a/ex/*/agents/planner*, a2a/ex/*/15/, a2a/ex/run/15/
- **검증:** 15 캡처 --check 4회 일치(메시 여섯 그대로), make all SKEL=1 rc=0 (1548장, 알림 0건)
- **비고:** 15부 133장으로 마무리. 동료의 CANCELED 를 REJECTED 로 옮기는 문제 등은 남겨 두었다.

### [2026-10-18 21:06] A2A 덱 15부 둘째 조각 — referenceTaskIds·진행 스트리밍·전 과정 실행(47장)
- **기획:** 견적 셋을 referenceTaskIds 로 정산에 넘기고, 기획 에이전트 자신의 SSE 를 보이고, 이야기 전체를 단일 메시 ×3 과 라틴 방진 꼴 섞인 메시 ×3 으로 돌린다.
- **TC:** 정상 — 메시 여섯 모두 §2.6 숫자(총 4,842,000, 잔액 1,158,000)와 요약 8/8 일치. 경계 — 다른 서버의 Task 를 가리키는 참조, 승인 뒤 이어 말하기.
- **개발:** a2a/deck/sections/15b_scenario.html, 15_scenario.html, a2a/ex/*/15/, a2a/ex/run/15/
- **검증:** 15 캡처 --check 4회 일치, make all SKEL=1 rc=0 (1519장, 알림 0건)
- **비고:** 어느 SDK 도 다른 서버의 referenceTaskIds 를 풀지 못한다. 승인 거절 때 정산 작업을 취소하지 않는 결함은 셋째 조각에서 다룬다.

### [2026-10-18 20:08] A2A 기획 에이전트 결함 4종 수정 ×3 — 메시지 이중 계산·전각 숫자·역할 확인·내부 주소 노출
- **기획:** 15부 첫 조각이 찾은 결함을 세 언어에서 같은 동작으로 고친다. 빠진 역할·닿지 않는 동료는 위임 전에 FAILED 로 끝내고 역할 이름만 알린다.
- **TC:** 골든 fullwidth-digits(파이썬만 RED), 기획 에이전트 시험 ×3 — 메시지 한 번만 세기(TS RED), 빠진 역할을 먼저 거절(셋 다 RED), 오류에 내부 주소 없음.
- **개발:** a2a/ex/*/agents/planner*, a2a/ex/py/workshop/domain.py, a2a/ex/fixtures/golden/domain.json, a2a/ex/*/15/, a2a/ex/run/15/, a2a/deck/sections/15_scenario.html 외 2개 파일
- **검증:** make golden·test 통과, 15 캡처 --check 4회 일치, make all SKEL=1 rc=0 (1473장, 알림 0건)
- **비고:** 15부 첫 조각은 56장. 9부 direct 캡처가 스왑 아래서 한 번 뒤집혔다 — 리뷰 때 볼 것.

### [2026-10-18 18:02] A2A 덱 15부 첫 조각 — 기획 에이전트 설계·레지스트리·동시 위임(50장)
- **기획:** 기획 에이전트의 흐름(발견→해석→팬아웃→정산→계획서), 카드와 스킬로 동료 찾기 ×3, 같은 contextId 로 동시 위임 ×3 을 보인다. 15부를 세 파일로 나눴다.
- **TC:** 정상 — 자유 문장 해석 일곱 ×3, 팬아웃 차례 고정(관문 프록시). 경계 — 빠진 항목 되묻기, 모르는 카드, 빠진 역할, 죽은 레지스트리 주소, 홀로 온 요청(504).
- **개발:** a2a/deck/sections/15_scenario.html, 15b_scenario.html, 15c_scenario.html, a2a/deck/order.txt, a2a/ex/*/15/, a2a/ex/run/15/, a2a/ex/*/agents/planner* 외 1개 파일
- **검증:** 15 캡처 --check 4회 일치, make all SKEL=1 rc=0 (1467장, 알림 0건)
- **비고:** 우리 기획 에이전트의 결함 4종(TS 메시지 이중 계산, 파이썬 전각 숫자, 역할 확인 없음, 내부 주소 노출)을 찾았다 — 다음 커밋에서 고친다.

### [2026-10-18 15:01] A2A 덱 14부 — 확장과 버전 협상(61장)
- **기획:** AgentExtension 선언·활성화, 이 책의 예산 확장 ×3, 판 협상 비교표, v0.3 피어와의 공존을 세 SDK 로 보인다.
- **TC:** 정상 — 예산 확장 3×3, v0.3 3×3. 경계 — 모르는 확장, 필수인데 안 켬(-32008), 한도 없음, 판 2.0·0.3·빈 값·1.0.1, 쿼리 판.
- **개발:** a2a/deck/sections/14_ext.html, 09_go.html, 09b_go.html, a2a/ex/*/14/, a2a/ex/run/14/, a2a/ex/go/go.mod 외 2개 파일
- **검증:** Go 바이너리 캐시를 비우고 전체 --check 230 일치, make all SKEL=1 rc=0 (1417장, 알림 0건)
- **비고:** 옛 a2a-go v0.3.15 를 받아 9부의 환경 캡처 둘이 사실대로 바뀌어 글을 고쳤다.

### [2026-10-18 14:28] A2A 실행기 Go 빌드 캐시가 같은 부의 도우미 패키지를 보게 고침
- **기획:** _go_build 가 예제 디렉터리만 해시해, 13/restmount·14/budget 같은 도우미 패키지를 고쳐도 낡은 바이너리를 다시 썼다. 장부처럼 부 디렉터리 전체를 키로 삼는다.
- **TC:** 같은 부의 도우미 패키지 상수를 바꾸면 출력이 따라 바뀌는지 보는 실제 Go 시험(RED: 옛 값 "하나" 출력).
- **개발:** a2a/tools/a2arun.py, a2a/tools/tests/test_a2arun.py
- **검증:** 도구 시험 147 통과

### [2026-10-18 11:06] A2A 덱 13부 뒤 절반 — gRPC ×3·한 서버 세 바인딩·스펙 어긋남(46장)
- **기획:** gRPC 서버·클라이언트 ×3 과 오류 → 상태 코드, 바인딩 셋을 한 카드에 단 서버와 클라이언트의 고르기, SubscribeToTask 동사 같은 스펙 어긋남을 보인다.
- **TC:** 정상 — gRPC 3×3 보내기·스트림. 경계 — 깨진 메시지, 없는 메서드·Task, 판 머리 없음·9.9, 죽은 gRPC 포트(되돌아감 없음), http:// 꼴 주소, PUT 구독.
- **개발:** a2a/deck/sections/13b_binding.html, 13_binding.html, 08_ts.html, 09_go.html, a2a/ex/*/13/, a2a/ex/run/13/, a2a/ex/go/go.mod, a2a/ex/ts/package.json 외 다수
- **검증:** 전체 --check(224) 뒤 바뀐 캡처 재확인 2회, make all SKEL=1 rc=0 (1358장, 알림 0건)
- **비고:** 13부 92장. gRPC 의존을 넣자 환경을 찍는 8·9부 캡처 셋이 바뀌어 글을 고쳤고, 11부 crud 예제의 경쟁 상태도 찾아 고쳤다.

### [2026-10-18 09:06] A2A 덱 13부 앞 절반 — 바인딩 동등성·메서드 대응표·HTTP+JSON ×3(46장)
- **기획:** 세 바인딩이 같아야 한다는 요구와 메서드 대응표를 proto 의 HTTP 규칙으로 보이고, 완성 에이전트를 세 서버의 REST 로 띄워 감청한다. 13부를 두 파일로 나눴다.
- **TC:** 정상 — REST 보내기·스트림·조회 ×3, 언어 교차 매트릭스. 경계 — 깨진 JSON, 없는 경로·Task, 테넌트 경로, 스트림 시작 전 오류.
- **개발:** a2a/deck/sections/13_binding.html, 13b_binding.html, a2a/deck/order.txt, a2a/ex/*/13/, a2a/ex/run/13/
- **검증:** 13 캡처 --check 2회 일치(1회는 스왑 탓 준비 시간 초과, 단독 재실행 4회 일치), make all SKEL=1 rc=0 (1313장, 알림 0건)
- **비고:** Go 클라이언트는 TS REST 서버의 오류를 읽지 못하고, Go 서버는 스트림 시작 오류를 200 SSE 안에 담는다.

### [2026-10-18 06:16] A2A 덱 12부 뒤 절반 — 스코프·확장 카드·AUTH_REQUIRED·서명된 카드(58장), 정산 스코프 검사 수정
- **기획:** 스코프, GetExtendedAgentCard, 작업 중 권한(AUTH_REQUIRED), JCS+JWS 서명 카드를 세 언어로 보이고, 우리 Bearer 검사가 카드의 payment:read 를 안 보던 결함을 고친다.
- **TC:** 정상 — 기획 에이전트의 결재 사슬, 서명·검증 ×3. 경계 — 스코프 모자란 토큰(403), 익명 확장 카드, 위조 카드와 jku, 모르는 필드를 더한 카드.
- **개발:** a2a/deck/sections/12b_security.html, 12_security.html, a2a/ex/*/12/, a2a/ex/run/12/, a2a/ex/*/agents/settlement* 외 3개 파일
- **검증:** 12 캡처 --check 4회 일치(기존 캡처 변화 0), make all SKEL=1 rc=0 (1268장, 어긋남 0건, 알림 0건)
- **비고:** 12부 119장. 결재 토큰이 문지기를 지나도록 기획 에이전트 ×3 도 payment:read 를 함께 청하게 바꿨다.

### [2026-10-18 04:26] A2A 덱 12부 앞 절반 — 전송 보안·보안 스킴·토큰 발급기·Bearer 검사(62장)
- **기획:** HTTPS 요구와 로컬 http 의 까닭, 카드의 securitySchemes·Requirements, 정산 에이전트 안의 OAuth2 발급기 ×3 과 Bearer 검사 ×3 을 캡처로 보인다. 12부를 두 파일로 나눴다.
- **TC:** 정상 — client_credentials 발급, 맞는 토큰. 경계 — 모르는 CA, grant_type 없음, Basic 인증, 토큰 없음·깨짐·모름, 카드만 있고 검사 없는 서버.
- **개발:** a2a/deck/sections/12_security.html, 12b_security.html, a2a/deck/order.txt, a2a/ex/*/12/, a2a/ex/run/12/
- **검증:** 12 캡처 --check 4회 일치, make all SKEL=1 rc=0 (1212장, 어긋남 0건)
- **비고:** 어느 SDK 서버도 카드의 보안 요구를 스스로 지키지 않는다. 우리 Bearer 검사가 payment:read 스코프를 안 보는 결함은 뒤 절반 5장에서 고친다.

### [2026-10-18 03:27] A2A 덱 11부 뒤 절반 — 푸시 설정 CRUD·취소·목록·웹훅 보안(53장), Go 교통 에이전트 푸시 인증 수정
- **기획:** 푸시 설정 조회·목록·삭제, CancelTask, ListTasks 필터·쪽, 웹훅 보안(SSRF·토큰·재전송)을 세 서버로 보이고, 우리 Go 에이전트의 §4.3.3 위반을 고친다.
- **TC:** 정상 — 설정 CRUD ×3, 진행 중 취소, 목록 필터. 경계 — 없는 설정·Task, 끝난 뒤 취소, pageSize 0·101, 사설 주소 웹훅, 같은 POST 재전송.
- **개발:** a2a/deck/sections/11b_push.html, 11_push.html, a2a/ex/*/11/, a2a/ex/run/11/, a2a/ex/go/agents/bus/main.go
- **검증:** 11 캡처 --check 3회 일치(내용이 바뀐 캡처는 auth.txt 하나), make all SKEL=1 rc=0 (1151장, 어긋남 0건)
- **비고:** 11부 116장. TS SDK 는 CANCELED 푸시를 두 번 보내고, Go SDK 는 없는 푸시 설정에 -32603 을 준다.

### [2026-10-18 00:49] A2A 덱 11부 앞 절반 — 교통 에이전트·폴링·푸시 설정·웹훅 수신기(63장)
- **기획:** 장기 작업을 받는 두 길(폴링·푸시)을 교통 에이전트 ×3 과 웹훅 수신기 ×3 으로 보이고, 세 SDK 서버가 실제로 보내는 푸시를 감청한다. 11부를 두 파일로 나눴다.
- **TC:** 정상 — 배차 3단계 ×3 서버, 웹훅 도착. 경계 — 늦게 만든 설정, id 없는 설정, 없는 Task, 푸시 없는 카드, 틀린 토큰과 401.
- **개발:** a2a/deck/sections/11_push.html, 11b_push.html, a2a/deck/order.txt, a2a/ex/*/11/, a2a/ex/run/11/, a2a/ex/*/agents/bus* 외 3개 파일
- **검증:** 11 캡처 --check 5회 일치, make all SKEL=1 rc=0 (1099장, 어긋남 0건)
- **비고:** 우리 Go 교통 에이전트가 AuthenticationInfo 를 무시한다(§4.3.3 MUST) — 뒤 절반 8장에서 고친다.

### [2026-10-18 00:49] A2A 실행기 서버 준비 대기 15초 → 60초
- **기획:** 11부 --check 에서 파이썬 SDK 서버가 스왑 탓에 15초 안에 못 떠 셋 중 둘이 실패했다(캡처 내용 차이는 0). 기다림만 늘리고 출력은 그대로 둔다.
- **TC:** 기본 대기가 60초 이상인지 보는 시험을 더해 RED 를 확인했다. 기존 2초 대기 시험은 그대로 통과.
- **개발:** a2a/tools/a2arun.py, a2a/tools/tests/test_a2arun.py
- **검증:** 도구 시험 146 통과, 11 캡처 --check 3회 일치

### [2026-10-17 21:33] A2A 덱 10부 뒤 절반 — 청크 다시 붙이기·재구독·파일 파트·스트림 미지원(59장)
- **기획:** 클라이언트에서 청크를 접는 법 ×3, SubscribeToTask 재구독과 여러 구독자, FilePart·DataPart, 스트리밍 미지원 카드를 캡처로 보인다.
- **TC:** 정상 — 식사 스트림 접기 ×3, 구독자 둘. 경계 — 모르는 artifactId 에 append, 끝난·없는 Task 구독, 멈춘 Task 재구독, 스트림 없는 카드에 구독.
- **개발:** a2a/deck/sections/10b_stream.html, 10_stream.html, a2a/ex/*/10/, a2a/ex/run/10/
- **검증:** 10 캡처 --check 5회 일치, make all SKEL=1 rc=0 (1037장, 어긋남 0건)
- **비고:** 10부 113장. Go 클라이언트가 JSON 오류를 빈 스트림으로 삼키는 결함을 찾았다. 재구독 캡처는 3초 간격에 기댄다.

### [2026-10-17 19:58] A2A 덱 10부 앞 절반 — 스트리밍 와이어·식사 에이전트·종료 규칙(54장)
- **기획:** SSE 이벤트 모델과 세 SDK 서버의 실제 차례, 식사 에이전트 ×3 의 청크 스트림, 스트림이 닫히는 때를 캡처로 보인다. 10부를 두 파일로 나눴다.
- **TC:** 정상 — 식사 스트림 ×3 서버 대조. 경계 — 종료 일곱 가지(AUTH_REQUIRED·WORKING 에서 돌아감, INPUT_REQUIRED 뒤 이벤트, 스트림 중 예외 등) ×3 서버.
- **개발:** a2a/deck/sections/10_stream.html, 10b_stream.html, 05b_task.html, a2a/deck/order.txt, a2a/ex/*/10/, a2a/ex/run/10/, a2a/ex/*/agents/catering* 외 2개 파일
- **검증:** 10 캡처 --check 4회 일치, make all SKEL=1 rc=0 (979장, 어긋남 0건)
- **비고:** 닫는 기준이 세 SDK 마다 달라 AUTH_REQUIRED 에서 TS·Go 는 §11.7 과 어긋난다. 2초 대기·0.3초 쉼에 기댄 캡처는 리뷰 때 다시 볼 것.

### [2026-10-17 18:34] A2A 덱 9부 뒤 절반 — Go SDK 클라이언트·완성 에이전트·시험·SDK 고유 기능(60장)
- **기획:** 7·8부 뒤 절반과 같은 장 구조로 Go 클라이언트, 숙소 에이전트 완성판, go test 시험, Go 만의 기능을 보이고 세 SDK 비교로 맺는다.
- **TC:** 정상 — 막는 호출·스트림, 되묻기 다중 턴과 골든 대조. 경계 — 손으로 단 판 머리글, 쉼표로 이은 확장 머리글, 실행기 패닉, 모르는 enum.
- **개발:** a2a/deck/sections/09b_go.html, 09_go.html, 07b_py.html, 08b_ts.html, a2a/ex/go/09/, a2a/ex/run/09/, a2a/ex/go/agents/lodging/main.go
- **검증:** 09 캡처 --check 3회 일치, make all SKEL=1 rc=0 (926장, 어긋남 0건)
- **비고:** 9부 127장(상한 132 이내). Go 숙소 에이전트를 동작 그대로 함수로 나눴고 Go 캡처 81개는 내용이 그대로다.

### [2026-10-17 17:39] A2A 덱 9부 앞 절반 — Go SDK 패키지·타입·실행기·처리기·서버(67장)
- **기획:** 7·8부와 같은 장 구조로 a2a-go v2.6.0 을 설치본 소스와 캡처로 읽고, 정리 표마다 세 SDK 를 나란히 둔다.
- **TC:** 정상 — 메아리·견적 단계 예제, 처리기 직접 호출, 서버 셋. 경계 — 반칙 실행기 일곱, 침묵 실행기, 판 머리글 없음, GET 요청, 낡은 판 갱신.
- **개발:** a2a/deck/sections/09_go.html, a2a/ex/go/09/, a2a/ex/run/09/, a2a/out/09/
- **검증:** 09 캡처 --check 3회 일치, make all SKEL=1 rc=0 (867장, 어긋남 0건)
- **비고:** 표지 둘을 감싼 오류의 JSON-RPC 코드가 맵 순회 탓에 무작위로 갈리는 SDK 결함을 찾았다.

### [2026-10-17 16:39] A2A 덱 8부 뒤 절반 — TypeScript SDK 클라이언트·완성 에이전트·시험·SDK 고유 기능(59장)
- **기획:** 7부 뒤 절반과 같은 장 구조로 TS 클라이언트, 숙소 에이전트 완성판, node --test 시험, TS 만의 기능을 보인다.
- **TC:** 정상 — 막는 호출·스트림, 되묻기 다중 턴과 골든 대조. 경계 — 모르는 응답 필드, 스트림 중 오류, 401 재시도, v0.3 호환 라우팅, 100 KB 넘는 본문.
- **개발:** a2a/deck/sections/08b_ts.html, 08_ts.html, a2a/ex/ts/08/, a2a/ex/run/08/, a2a/ex/ts/agents/lodging.ts
- **검증:** 08 캡처 --check 3회 일치, make all SKEL=1 rc=0 (802장, 어긋남 0건)
- **비고:** 8부 126장(예산 120, +10 % 이내). lodging.ts 에 region 표시를 더해 TS 캡처 85개를 다시 떴고 내용은 그대로다.

### [2026-10-17 15:35] A2A 덱 8부 앞 절반 — TypeScript SDK 패키지·타입·실행기·처리기·서버(67장)
- **기획:** 7부와 같은 장 구조로 @a2a-js/sdk 1.3.0 의 진입점·ts-proto 타입·실행기·처리기·express 서버를 설치본 소스와 캡처로 보인다.
- **TC:** 정상 — 메아리·견적 단계 예제, 처리기 직접 호출, 서버 셋. 경계 — 반칙 실행기 일곱, 침묵 실행기, 판 머리글 없음, JSON 아님, 경로 밖 요청.
- **개발:** a2a/deck/sections/08_ts.html, a2a/ex/ts/08/, a2a/ex/run/08/, a2a/out/08/
- **검증:** 08 캡처 --check 4회 일치, make all SKEL=1 rc=0 (744장, 어긋남 0건)
- **비고:** 막는 호출에는 차례 검사가 없고, 익명 Task 의 소유자가 "unknown" 이라 같은 이름의 사용자와 섞인다.

---
## Archive
- [2026-10](history/archive/history-2026-10.md) — 59 entries
- [2026-09](history/archive/history-2026-09.md) — 161 entries
