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
| kubectl | v1.37.0 (kustomize v5.8.1) | 2026-09-08 | `kubectl kustomize` 만 오프라인으로 된다 |
| kubeconform | v0.8.0 | 2026-09-08 | 스키마는 kubernetes-json-schema `master-standalone-strict` |
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
| `w-tls-5b` | `idp-signing.key` 는 RSA 2048비트 개인키 하나뿐이고 인증서가 없다 (4부 토큰 서명용) | A | `certs/check_certs.sh` 출력 | 2026-09-08 |

- RFC 6125 (Representation and Verification of Domain-Based Application Service Identity) — https://www.rfc-editor.org/rfc/rfc6125#section-6.4.4

## 1부 — 웹 (`w-*` 슬라이드)

| 슬라이드 | 주장 | 등급 | 출처 | 확인일 |
|---|---|---|---|---|
| `w-url-4` | 리눅스에서 1024 미만 포트를 열려면 특권이 필요하다 | C | `man 7 ip` (`ip_unprivileged_port_start`) | 2026-09-08 |
| `w-url-4` | LDAP 389 · LDAPS 636 · 글로벌 카탈로그 3268/3269 | C | Microsoft Learn "Active Directory 및 Active Directory 도메인 서비스 포트 요구 사항" | 2026-09-08 |
| `w-http-2` | HTTP 요청의 줄 끝은 CRLF, 헤더 끝은 빈 줄 | A | `out/web01_trace.txt` (82바이트 · 0050 이 빈 줄) | 2026-09-08 |
| `w-http-2` | 같은 규정의 근거 | C | RFC 9112 §2.1 (HTTP/1.1 메시지 문법) | 2026-09-08 |
| `w-http-9` | Go 의 헤더 지도는 순회 순서가 정해져 있지 않다 | C | Go 명세 "For statements with range clause" — 지도의 순회 순서는 정해지지 않음 | 2026-09-08 |
| `w-http-10` | `Host` 는 `r.Header` 에서 빠져 `r.Host` 에 담긴다 | A | `out/web01_echo.txt` 와 `web/01_hello/main.go` | 2026-09-08 |
| `w-st-2` | 401 은 인증 실패, 403 은 인가 실패 | C | RFC 9110 §15.5.2 · §15.5.4 | 2026-09-08 |
| `w-rd-1` | 3xx 의 다음 주소는 `Location` 헤더에 온다 | A | `out/web03_nofollow.txt` 13–21행 | 2026-09-08 |
| `w-rd-5` | `Location` 은 상대 주소여도 된다 | C | RFC 7231 §7.1.2 (현행 RFC 9110 §10.2.2) | 2026-09-08 |
| `w-rd-8` | 303 은 방법을 GET 으로 바꾸고 307 은 그대로 둔다 | A | `out/web03_post_303.txt` · `out/web03_post_307.txt` | 2026-09-08 |
| `w-rd-8` | 301/302 에 대해 브라우저가 POST 를 GET 으로 바꾸는 것은 규약 위반이나 관행 | C | RFC 9110 §15.4.2 註 · §15.4.3 註 | 2026-09-08 |
| `w-fm-2` | 폼 전송의 기본 형식은 `application/x-www-form-urlencoded` | A | `out/web02_login_ok.txt` 7–15행 | 2026-09-08 |
| `w-ck-2` | `Set-Cookie` 의 값·속성 구조 | A | `out/web02_login_ok.txt` 19행 | 2026-09-08 |
| `w-ck-3` | 쿠키 속성 `Path`·`HttpOnly`·`SameSite`·`Max-Age`·`Secure` 의 뜻 | C | RFC 6265 §4.1.2, RFC 6265bis §5.4 (SameSite) | 2026-09-08 |
| `w-ck-4` | 브라우저(=curl)의 쿠키 저장 칸 구성 | A | `out/web02_jar_loggedin.txt` | 2026-09-08 |
| `w-ck-7` | 세션 번호는 `crypto/rand` 16바이트 = 2^128 가지 | A | `web/02_form_cookie/main.go` · `web/02_form_cookie/main_test.go` | 2026-09-08 |
| `w-ck-12` | 쿠키를 지우는 방법은 수명이 끝난 같은 이름의 쿠키를 다시 주는 것 | A | `out/web02_logout.txt` 17행 (`Max-Age=0`) | 2026-09-08 |
| `w-tls-5` | 요즘 클라이언트는 CN 이 아니라 SAN 으로 이름을 확인한다 | C | RFC 6125 §6.4.4 · CA/Browser Forum BR 7.1.4.2 | 2026-09-08 |
| `w-tls-7` | 신뢰하지 않는 CA → `unable to get local issuer certificate` | A | `out/web04_notrust.txt` 41–48행 | 2026-09-08 |
| `w-tls-9` | 이름이 다르면 CA 를 믿어도 거절한다 | A | `out/web04_wrongname.txt` 41–42행 | 2026-09-08 |
| `w-tls-13` | Go 의 HTTPS 서버는 ALPN 으로 HTTP/2 를 협상하고, HTTP/2 는 헤더 이름을 소문자로 못 박는다 | A + C | `out/web04_trust.txt` 53–66행 · RFC 9113 §8.2.1 | 2026-09-08 |
| `w-tb-1` | 예시 JSON 의 정형화 | A | `out/tool_json.txt` 1–9행 | 2026-09-08 |
| `w-tb-2` | JSON 은 마지막 쉼표를 허용하지 않는다 | A | `out/tool_json.txt` 11–12행 | 2026-09-08 |
| `w-tb-4` | base64url 은 `+`→`-`, `/`→`_`, `=` 제거 | C | RFC 4648 §5 | 2026-09-08 |
| `w-tb-6` | SHA-256 은 같은 입력에 같은 값, 한 글자만 달라도 전부 달라짐 | A | `out/tool_hash.txt` | 2026-09-08 |
| `w-tb-8` | 개인키로 서명하고 공개키로 확인하며, 내용이 바뀌면 확인이 실패한다 | A | `out/tool_sign.txt` | 2026-09-08 |
| `w-tb-10` | YAML 은 탭을 들여쓰기로 쓸 수 없다 | C | YAML 1.2.2 §6.1 "Indentation Spaces" | 2026-09-08 |

**캡처를 만든 방법** — 전부 `sh tools/record.sh` 한 번으로 나온다.
세 번 돌려 md5 가 모두 같은 것을 확인했다(2026-09-08).
매번 달라지는 값(시각·세션 번호·임시 포트·OpenSSL 오류 식별자)만
`tools/scrub.py` 가 고정값으로 바꾼다 — 해시나 상태 번호 같은
**뜻이 있는 값은 건드리지 않는다**.

## 3부 — AD·LDAP (`ad-*` 슬라이드)

| 슬라이드 | 주장 | 등급 | 출처 | 확인일 |
|---|---|---|---|---|
| `ad-dir-3` | DN 은 왼쪽이 자신, 오른쪽으로 갈수록 상위. DC 를 이으면 도메인 이름 | C | RFC 4514 §2 | 2026-09-08 |
| `ad-attr-1` | `sAMAccountName` 은 도메인 안에서 유일하고 20자 제한 | C | Microsoft Learn "sAMAccountName attribute" | 2026-09-08 |
| `ad-attr-1` | UPN 은 숲 전체에서 유일 | C | Microsoft Learn "userPrincipalName attribute" | 2026-09-08 |
| `ad-attr-2` | AD 사용자의 objectClass 는 top·person·organizationalPerson·user | A | `data/campus.ldif` · `out/ad_search_filters.txt` | 2026-09-08 |
| `ad-attr-3` | `objectGUID` 는 16바이트 이진값이고 변하지 않는다 | A + C | `out/ad_search_bytes.txt` 64–68행 · Microsoft Learn "objectGUID attribute" | 2026-09-08 |
| `ad-attr-4` | uAC 512 보통 · 514 비활성 · 66048 만료 없음 (0x0002 / 0x0200 / 0x10000) | A + C | `data/campus.ldif` · Microsoft Learn "How to use the UserAccountControl flags" | 2026-09-08 |
| `ad-grp-2` | `memberOf` 는 저장된 값이 아니라 역참조로 계산된다 | A + C | `ldap/fakead/dir.go` `indexGroups` · Microsoft Learn "memberOf attribute" | 2026-09-08 |
| `ad-ber-1` | BER 은 TLV(태그·길이·내용) 구조 | C | ITU-T X.690 §8.1 | 2026-09-08 |
| `ad-ber-3` | 길이 128 은 `81 80`, `80` 하나는 부정 길이라 LDAP 에서 금지 | A + C | `ldap/ber/ber_test.go` 골든 · RFC 4511 §5.1 | 2026-09-08 |
| `ad-ber-4` | 정수는 2의 보수·빅엔디언·최소 길이 (128 = `00 80`) | A + C | `ber_test.go` 골든 표 · X.690 §8.3 | 2026-09-08 |
| `ad-ber-9` | 익명 바인드는 `30 0C 02 01 01 60 07 02 01 03 04 00 80 00` | A + C | `ber_test.go` 골든 · RFC 4511 §4.2 | 2026-09-08 |
| `ad-bind-1` | LDAP 은 연결 단위로 신분을 기억한다 | C | RFC 4511 §4.2.1 | 2026-09-08 |
| `ad-bind-2` | simple bind 는 비밀번호를 평문으로 보낸다 | A + C | `out/ad_bind_ok.txt` · RFC 4511 §4.2 | 2026-09-08 |
| `ad-bind-4` | AD 는 실패 이유를 전부 49 로 답하고 `data XXX` 로만 알린다 | A + C | `out/ad_bind_52e.txt` 등 · Microsoft Learn "LDAP error codes" | 2026-09-08 |
| `ad-bind-5` | data 525·52e·530·531·532·533·701·773·775 의 뜻 | C | Microsoft Learn "Active Directory LDAP 바인드 오류" | 2026-09-08 |
| `ad-bind-7` | 실패가 잦으면 잠긴다 (우리 흉내: 창 10분·5회·잠금 30분) | A | `out/ad_bind_775.txt` · `ldap/fakead/dir.go` | 2026-09-08 |
| `ad-bind-8` | 비밀번호가 빈 바인드(unauthenticated bind)는 성공으로 처리하면 안 된다 | C | RFC 4511 §4.2 · RFC 4513 §5.1.2 | 2026-09-08 |
| `ad-srch-1` | SearchRequest 는 여덟 칸이고 순서로만 구별된다 | A + C | `out/ad_search_bytes.txt` · RFC 4511 §4.5.1 | 2026-09-08 |
| `ad-srch-2` | scope 는 base(0)·one(1)·sub(2) | A + C | `out/ad_search_scopes.txt` · RFC 4511 §4.5.1.2 | 2026-09-08 |
| `ad-srch-3` | 필터 문법 (`&` `|` `!` `=` `=*` `>=` `<=` `~=`) | A + C | `out/ad_search_filters.txt` · RFC 4515 §3 | 2026-09-08 |
| `ad-srch-6` | 필터 값의 `( ) * \` 와 NUL 은 `\XX` 로 이스케이프 | A + C | `ldap/proto/proto_test.go` · RFC 4515 §3 | 2026-09-08 |
| `ad-srch-7` | present 필터만 원시형이라 태그가 `87` | A + C | `proto_test.go` 골든 · RFC 4511 §4.5.1.7 | 2026-09-08 |
| `ad-srch-13` | AD 는 한 검색에서 기본 1000건만 돌려준다 | C | Microsoft Learn "MaxPageSize" (LDAP 정책 기본값 1000) | 2026-09-08 |
| `ad-srch-13` | Simple Paged Results 컨트롤 OID 는 1.2.840.113556.1.4.319 | A + C | `ldap/proto/proto.go` · RFC 2696 | 2026-09-08 |
| `ad-tls-1` | 포트 389 LDAP · 636 LDAPS · 3268/3269 글로벌 카탈로그 | C | Microsoft Learn "AD DS 포트 요구 사항" | 2026-09-08 |
| `ad-tls-3` | 사내 CA 를 안 믿으면 악수가 깨진다 (자바 쪽 PKIX path building failed) | A + C | `out/ad_ldaps_notrust.txt` · 1부 7장 | 2026-09-08 |
| `ad-tls-4` | AD 는 익명 검색을 기본으로 막는다 → 서비스 계정이 필요하다 | A + C | `out/ad_search_nobind.txt` · Microsoft Learn "익명 LDAP 작업" | 2026-09-08 |
| `ad-not-2` | StartTLS · SASL/GSSAPI · referral · GC 는 흉내 내지 않는다 | A | `ldap/fakead/server.go` 머리말 · `unwillingToPerform(53)` | 2026-09-08 |
| `ad-not-3` | Kerberos 는 비밀번호 대신 티켓을 보낸다 | C | RFC 4120 §1.1 · Microsoft Learn "Kerberos 인증 개요" | 2026-09-08 |

**RFC 목록** — 4511(프로토콜) · 4513(인증·보안) · 4514(DN 표현) ·
4515(필터 표현) · 2696(페이지) · 2849(LDIF) · ITU-T X.690(BER).

**가짜 AD 의 재현 범위** — `ldap/fakead/server.go` 머리말에 "하는 것/안 하는 것" 을
적어 두었고, 3부 8장이 그 목록을 그대로 슬라이드로 보여 준다.
안 하는 것을 조용히 무시하지 않고 `unwillingToPerform(53)` 으로 거절한다.

## 4부 — OAuth 2.0 · OIDC (`so-*` 슬라이드)

| 슬라이드 | 주장 | 등급 | 출처 | 확인일 |
|---|---|---|---|---|
| `so-why-7` | OIDC 는 OAuth 2.0 **위에** 얹은 층이고, ID 토큰을 더한다 | C | OIDC Core 1.0 §1 (Overview) | 2026-09-08 |
| `so-flow-5` | client_id·redirect_uri 가 확인되기 전에는 그 주소로 오류를 보내면 안 된다 | C | RFC 6749 §4.1.2.1 | 2026-09-08 |
| `so-flow-9` | 인가 코드는 짧고(권고 10분 이하) **한 번만** 쓴다 | C | RFC 6749 §4.1.2 | 2026-09-08 |
| `so-flow-12` | 토큰 응답에 `Cache-Control: no-store` 를 붙인다 | C | RFC 6749 §5.1 | 2026-09-08 |
| `so-flow-13` | implicit 흐름은 더 쓰지 않기를 권고한다 | C | OAuth 2.0 Security BCP(RFC 9700) §2.1.2 · OAuth 2.1 초안 | 2026-09-08 |
| `so-flow-14` | 같은 코드를 두 번 내밀면 `invalid_grant` 로 거절된다 | A | `out/oidc_token_replay.txt` | 2026-09-08 |
| `so-guard-6` | challenge = base64url(SHA-256(verifier)), method `S256` | C | RFC 7636 §4.2 | 2026-09-08 |
| `so-guard-8` | verifier 는 43~128글자의 unreserved 문자 | C | RFC 7636 §4.1 | 2026-09-08 |
| `so-guard-9` | verifier 가 틀리면 코드가 멀쩡해도 `invalid_grant` | A | `out/oidc_token_badverifier.txt` | 2026-09-08 |
| `so-guard-10` | PKCE 를 모든 클라이언트에 권고한다 | C | OAuth 2.1 초안 §4.1.1 · RFC 9700 §2.1.1 | 2026-09-08 |
| `so-token-3` | 액세스 토큰의 `typ` 은 `at+jwt` | C | RFC 9068 §2.1 | 2026-09-08 |
| `so-token-4` | `Authorization: Bearer <토큰>` 으로 보낸다 | C | RFC 6750 §2.1 | 2026-09-08 |
| `so-token-6` | 401 에는 `WWW-Authenticate: Bearer` 를 붙인다 | C | RFC 6750 §3 | 2026-09-08 |
| `so-token-8` | 리프레시 토큰 회전 — 재사용은 탈취 신호로 다룬다 | C | RFC 9700 §4.14 | 2026-09-08 |
| `so-jwt-1` | `머리.내용.서명` 은 JWS Compact Serialization | C | RFC 7515 §3.1 | 2026-09-08 |
| `so-jwt-5` | `iss·sub·aud·exp·nbf·iat·jti` 는 등록된 클레임 | C | RFC 7519 §4.1 | 2026-09-08 |
| `so-jwt-5` | 시각 클레임은 1970년부터 센 초(NumericDate) | C | RFC 7519 §2 | 2026-09-08 |
| `so-jwt-8` | RS256 = RSASSA-PKCS1-v1_5 + SHA-256 | C | RFC 7518 §3.3 | 2026-09-08 |
| `so-jwt-11` | 내용을 고치면 서명이 어긋난다 (실제 출력) | A | `out/oidc_verify_tampered.txt` | 2026-09-08 |
| `so-jwt-13` | `alg=none` 과 알고리즘 혼동(RS256→HS256)은 알려진 공격이다 | C | RFC 8725 §2.1·§2.2·§3.1 | 2026-09-08 |
| `so-jwt-14` | 서명 확인만으로 부족하고 `iss`·`aud`·`exp` 를 함께 본다 | C | RFC 8725 §3.8·§3.9 · OIDC Core §3.1.3.7 | 2026-09-08 |
| `so-jwks-2` | JWKS 의 RSA 공개키는 `n`·`e` 로 이뤄진다 (`AQAB` = 65537) | A·C | `out/oidc_certs_short.txt` · RFC 7518 §6.3.1 | 2026-09-08 |
| `so-jwks-4` | `kid` 로 열쇠를 고른다 (키 회전) | C | RFC 7517 §4.5 | 2026-09-08 |
| `so-jwks-5` | 안내문 경로는 `/.well-known/openid-configuration` | C | OIDC Discovery 1.0 §4 · RFC 8615 | 2026-09-08 |
| `so-jwks-7` | 안내문의 `issuer` 가 부른 주소와 같아야 한다 | C | OIDC Discovery 1.0 §4.3 | 2026-09-08 |
| `so-out-5` | 로그아웃에 `id_token_hint` 를 보낸다 | C | OIDC RP-Initiated Logout 1.0 §2 | 2026-09-08 |
| `so-out-7` | 로그아웃 귀환 주소는 별도 목록으로 등록한다 | A·C | `out/oidc_app_logout.txt` · OIDC RP-Initiated Logout §2 | 2026-09-08 |
| `so-jwt-quiz` | 토큰 내용을 감추려면 서명이 아니라 암호화(JWE)가 필요하다 | C | RFC 7516 §1 | 2026-09-08 |
| `so-out-9` | 이미 나간 JWT 는 회수할 수 없다 — 짧은 수명 · introspection · 취소 목록 | C | RFC 7662 §1 · RFC 9700 §2.2.2 | 2026-09-08 |

- RFC 6749 (OAuth 2.0) — https://www.rfc-editor.org/rfc/rfc6749 · 확인 2026-09-08
- RFC 6750 (Bearer Token Usage) — https://www.rfc-editor.org/rfc/rfc6750 · 확인 2026-09-08
- RFC 7515 (JWS) — https://www.rfc-editor.org/rfc/rfc7515 · 확인 2026-09-08
- RFC 7516 (JWE) — https://www.rfc-editor.org/rfc/rfc7516 · 확인 2026-09-08
- RFC 7517 (JWK) — https://www.rfc-editor.org/rfc/rfc7517 · 확인 2026-09-08
- RFC 7518 (JWA) — https://www.rfc-editor.org/rfc/rfc7518 · 확인 2026-09-08
- RFC 7519 (JWT) — https://www.rfc-editor.org/rfc/rfc7519 · 확인 2026-09-08
- RFC 7662 (Token Introspection) — https://www.rfc-editor.org/rfc/rfc7662 · 확인 2026-09-08
- RFC 7636 (PKCE) — https://www.rfc-editor.org/rfc/rfc7636 · 확인 2026-09-08
- RFC 8615 (Well-Known URIs) — https://www.rfc-editor.org/rfc/rfc8615 · 확인 2026-09-08
- RFC 8725 (JWT Best Current Practices) — https://www.rfc-editor.org/rfc/rfc8725 · 확인 2026-09-08
- RFC 9068 (JWT Profile for OAuth 2.0 Access Tokens) — https://www.rfc-editor.org/rfc/rfc9068 · 확인 2026-09-08
- RFC 9700 (OAuth 2.0 Security Best Current Practice) — https://www.rfc-editor.org/rfc/rfc9700 · 확인 2026-09-08
- OAuth 2.1 초안 — https://datatracker.ietf.org/doc/html/draft-ietf-oauth-v2-1 · 확인 2026-09-08
- OpenID Connect Core 1.0 — https://openid.net/specs/openid-connect-core-1_0.html · 확인 2026-09-08
- OpenID Connect Discovery 1.0 — https://openid.net/specs/openid-connect-discovery-1_0.html · 확인 2026-09-08
- OpenID Connect RP-Initiated Logout 1.0 — https://openid.net/specs/openid-connect-rpinitiated-1_0.html · 확인 2026-09-08

## 2부 — 쿠버네티스 (`k8-*` 슬라이드)

내려받은 도구의 sha256 (linux/arm64):

| 것 | 판 | sha256 | 받은 곳 |
|---|---|---|---|
| kubectl | v1.37.0 | `922df28df248cc00a9e025f947704f1d1482de64ece54cfe57e61f19eaf1eef3` | https://dl.k8s.io/release/v1.37.0/bin/linux/arm64/kubectl |
| kubeconform | v0.8.0 | `7e77b104b3ae696389f91971c60fd58c72f1f3dc218f139df67a1b070959c012` | https://github.com/yannh/kubeconform/releases/tag/v0.8.0 |

JSON 스키마 7개는 `master-standalone-strict` 판이다
(https://github.com/yannh/kubernetes-json-schema). 파일별 sha256 은
`sha256sum bin/schemas/*.json` 으로 언제든 다시 뜬다 —
`tools/fetch_k8s_tools.sh` 가 같은 주소에서 받는다.

| 슬라이드 | 주장 | 등급 | 출처 | 확인일 |
|---|---|---|---|---|
| `k8-box-3` | 컨테이너는 호스트 커널을 함께 쓰고, 네임스페이스와 c그룹으로 갈린다 | C | Kubernetes 문서 "Containers" 개요 | 2026-09-08 |
| `k8-box-5` | 쿠버네티스는 선언한 상태로 현실을 맞춘다 | C | Kubernetes 문서 "Kubernetes Objects" | 2026-09-08 |
| `k8-pod-1` | Pod 의 컨테이너는 더하거나 뺄 수 없고 최소 하나여야 한다 | C | `out/k8s_explain_pod_spec_containers.txt` (공식 JSON 스키마) | 2026-09-08 |
| `k8-dep-2` | selector 와 template 의 라벨이 어긋나면 거절된다 | C | Kubernetes 문서 "Deployment" — Selector | 2026-09-08 |
| `k8-dep-3` | `spec.replicas` 의 기본값은 1 | C | `out/k8s_explain_deployment_spec_replicas.txt` | 2026-09-08 |
| `k8-dep-3` | `spec.selector` 는 apps/v1 에서 만든 뒤 바꿀 수 없다 | C | Kubernetes 문서 "Deployment" — Selector updates (스키마에는 이 말이 없다) | 2026-09-08 |
| `k8-dep-7` | readiness 실패는 endpoints 에서 빼고, liveness 실패는 컨테이너를 다시 띄운다 | C | Kubernetes 문서 "Configure Liveness, Readiness and Startup Probes" | 2026-09-08 |
| `k8-dep-8` | 메모리 limits 초과는 OOMKilled, CPU 초과는 throttle | C | Kubernetes 문서 "Resource Management for Pods and Containers" | 2026-09-08 |
| `k8-svc-4` | Service 의 기본 종류는 ClusterIP | C | `out/k8s_explain_service_spec_type.txt` | 2026-09-08 |
| `k8-svc-5` | 클러스터 안 DNS 이름은 `<svc>.<ns>.svc.cluster.local` | C | Kubernetes 문서 "DNS for Services and Pods" | 2026-09-08 |
| `k8-ing-1` | Ingress 는 컨트롤러가 있어야 동작한다 | C | Kubernetes 문서 "Ingress Controllers" | 2026-09-08 |
| `k8-ing-3` | `pathType` 은 Exact · Prefix · ImplementationSpecific | C | `out/k8s_explain_ingress_spec_rules.txt` · Ingress 문서 | 2026-09-08 |
| `k8-cfg-1` | Secret 은 base64 로 담길 뿐 암호화가 아니다 | C | Kubernetes 문서 "Secrets" — Risks | 2026-09-08 |
| `k8-cfg-3` | 네임스페이스는 보안 경계가 아니다 (통신은 기본 허용) | C | Kubernetes 문서 "Network Policies" | 2026-09-08 |
| `k8-cfg-quiz` | 환경 변수로 넣은 Secret 값은 Pod 재시작 전까지 안 바뀐다 | C | Kubernetes 문서 "Secrets" — Mounted Secrets are updated automatically | 2026-09-08 |
| `k8-kz-4` | overlay 의 patch 문법은 JSON Patch | C | RFC 6902 · Kustomize 문서 | 2026-09-08 |
| `k8-val-1` | kubectl v1.37.0 · kubeconform v0.8.0 을 썼다 | A | `out/k8s_tools.txt` | 2026-09-08 |
| `k8-val-2` | `kubectl explain` 과 `--dry-run=client` 는 클러스터가 있어야 한다 | A | `out/k8s_needs_server.txt` | 2026-09-08 |
| `k8-val-6` | base·dev·prod 세 벌이 스키마 검사를 통과한다 | A | `out/k8s_validate.txt` | 2026-09-08 |
| `k8-val-9` | `-strict` 는 스키마에 없는 필드를 잡지만 `requests` 안의 오타는 못 잡는다 | A | `out/k8s_invalid.txt` | 2026-09-08 |
| `k8-val-10` | `-strict` 없이는 모르는 필드가 조용히 지나간다 | A | `out/k8s_invalid_nostrict.txt` | 2026-09-08 |
| `k8-val-11` | 쿠버네티스의 파서에서 따옴표 없는 `yes`·`NO`·`12:30` 은 **글자로 남는다** | A | `out/k8s_yaml_traps.txt` | 2026-09-08 |
| `k8-val-11b` | 같은 파서에서 `1.20` 은 1.2 로, `010` 은 8로 바뀐다 | A | `out/k8s_yaml_traps.txt` | 2026-09-08 |
| `k8-val-11b` | "노르웨이 문제" 는 `yes`/`no` 를 참·거짓으로 읽던 YAML 1.1 의 것이다 | C | YAML 1.1 §10.1 (bool) 대 YAML 1.2 core schema | 2026-09-08 |

- Kubernetes 문서 — https://kubernetes.io/docs/concepts/ · 확인 2026-09-08
- YAML 1.2 규격 — https://yaml.org/spec/1.2.2/ · 확인 2026-09-08
- Kustomize 문서 — https://kubectl.docs.kubernetes.io/references/kustomize/ · 확인 2026-09-08
- RFC 6902 (JSON Patch) — https://www.rfc-editor.org/rfc/rfc6902 · 확인 2026-09-08

## 앞으로 채울 곳

부가 하나씩 들어올 때마다 그 부의 절을 여기에 연다.
지금은 비어 있는 것이 정상이다 — 뼈대 커밋에는 주장이 거의 없다.

- [ ] 5부 Keycloak — 관리자 가이드 (버전 박힌 URL)
- [ ] 6부 k8s 배포 — Keycloak 서버 가이드 `all-config`
- [ ] 7부 AD 연동 — LDAP user federation 문서 + Microsoft Learn
- [ ] 8부 앱 연동 — oauth2-proxy · ingress-nginx `auth_request`
- [ ] 9부 권한 — 그룹·역할 매퍼
- [ ] 10부 운영 — 수명 기본값 · 이벤트 · 메트릭
