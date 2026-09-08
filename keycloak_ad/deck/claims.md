# 근거 대장 (claims.md)

이 덱이 사실이라고 주장하는 것들의 출처를 모아 둔 곳이다.
버전·포트·기본값·RFC 절 번호·AD 속성의 의미를 말하는 슬라이드는
**빠짐없이** 여기에 한 줄이 있어야 한다.

왜 따로 두나: 덱 본문에 URL 을 늘어놓으면 읽는 흐름이 끊기고, 몇 달 뒤
"이 값 어디서 봤더라" 를 다시 찾게 된다. 주장과 출처를 한 곳에 모아 두면
다음 리뷰에서 한 줄씩 다시 눌러 볼 수 있다.

## 적는 법

| 열 | 뜻 |
|---|---|
| 슬라이드 | 그 주장이 실린 슬라이드 `id` (예: `ch07-vendor-ad`) |
| 주장 | 한 줄로. 숫자·기본값·이름을 그대로 |
| 등급 | A 실행 검증 · B 구문 검증 · C 문서 근거 |
| 출처 | URL 또는 `out/파일명`. 문서는 **버전이 박힌 URL** 로 |
| 확인일 | 실제로 눌러 본 날 (YYYY-MM-DD) |

등급 A 는 출처 자리에 `out/` 아래 캡처 파일 이름을 적는다 — 그 파일이 곧 증거다.
등급 C 는 반드시 URL 이 있어야 하고, 없으면 그 주장은 덱에서 뺀다.

## 도구 버전

이 덱의 모든 tier A·B 출력은 아래 도구로 만들었다.
버전이 다르면 출력이 조금씩 다를 수 있다.

| 도구 | 버전 | 확인일 | 비고 |
|---|---|---|---|
| Go | 1.27.0 (android/arm64) | 2026-09-08 | `GOTOOLCHAIN=local`, 의존성 0 |
| Python | 3.14.4 | 2026-09-08 | 덱 조립기 · 글꼴 서브셋 |
| Node.js | 24.18.0 | 2026-09-08 | `deck/check_deck.js` (DOM 스텁) |
| OpenSSL | (아래 §인증서) | 2026-09-08 | 시연용 CA·서버 인증서 |
| Java | OpenJDK 21.0.12 | 2026-09-08 | Keycloak 배포판 실행용 |
| kubectl | (내려받은 뒤 기록) | — | tier B 검증 |
| kubeconform | (내려받은 뒤 기록) | — | tier B 검증 |
| Keycloak | (`keycloak/VERSION` 에 고정) | — | 26.x GA |

## 이름 규칙 (전부 지어낸 것)

| 것 | 이름 | 근거 |
|---|---|---|
| 예제 도메인 | `campus.example` | RFC 2606 §2 — `.example` 은 문서용으로 예약 |
| AD 도메인 | `ad.campus.example` / `DC=ad,DC=campus,DC=example` | 위와 같음 |
| 사람·그룹·realm·client | `minji`, `lunch-users`, `campus`, `lunch-web` | 지어낸 이름. 실존 조직과 무관 |

- RFC 2606 (Reserved Top Level DNS Names) — https://www.rfc-editor.org/rfc/rfc2606 · 확인 2026-09-08

## 인증서 (`certs/`)

| 슬라이드 | 주장 | 등급 | 출처 | 확인일 |
|---|---|---|---|---|
| (뼈대) | 자체 CA 로 서명한 서버 인증서 두 장이 `openssl verify` 를 통과한다 | A | `certs/check_certs.sh` 출력 | 2026-09-08 |
| (뼈대) | 요즘 TLS 클라이언트는 CN 이 아니라 SAN 으로 호스트 이름을 확인한다 | C | RFC 6125 §6.4.4, CA/Browser Forum BR 7.1.4.2 | 2026-09-08 |

- RFC 6125 (Representation and Verification of Domain-Based Application Service Identity) — https://www.rfc-editor.org/rfc/rfc6125#section-6.4.4

## 앞으로 채울 곳

부가 하나씩 들어올 때마다 그 부의 절을 여기에 연다.
지금은 비어 있는 것이 정상이다 — 뼈대 커밋에는 주장이 거의 없다.

- [ ] 1부 웹 — HTTP 상태 코드 · 쿠키 속성 · TLS
- [ ] 2부 쿠버네티스 — 오브젝트 필드 기본값
- [ ] 3부 AD·LDAP — RFC 4511/4513/4515/4519, RFC 2696, AD 속성과 오류 코드
- [ ] 4부 OAuth2·OIDC — RFC 6749/6750/7636/7519/7517/8414, OIDC Core·Discovery·Logout
- [ ] 5부 Keycloak — 관리자 가이드 (버전 박힌 URL)
- [ ] 6부 k8s 배포 — Keycloak 서버 가이드 `all-config`
- [ ] 7부 AD 연동 — LDAP user federation 문서 + Microsoft Learn
- [ ] 8부 앱 연동 — oauth2-proxy · ingress-nginx `auth_request`
- [ ] 9부 권한 — 그룹·역할 매퍼
- [ ] 10부 운영 — 수명 기본값 · 이벤트 · 메트릭
