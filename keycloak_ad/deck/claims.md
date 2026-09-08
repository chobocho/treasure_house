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

## 앞으로 채울 곳

부가 하나씩 들어올 때마다 그 부의 절을 여기에 연다.
지금은 비어 있는 것이 정상이다 — 뼈대 커밋에는 주장이 거의 없다.

- [ ] 2부 쿠버네티스 — 오브젝트 필드 기본값
- [ ] 4부 OAuth2·OIDC — RFC 6749/6750/7636/7519/7517/8414, OIDC Core·Discovery·Logout
- [ ] 5부 Keycloak — 관리자 가이드 (버전 박힌 URL)
- [ ] 6부 k8s 배포 — Keycloak 서버 가이드 `all-config`
- [ ] 7부 AD 연동 — LDAP user federation 문서 + Microsoft Learn
- [ ] 8부 앱 연동 — oauth2-proxy · ingress-nginx `auth_request`
- [ ] 9부 권한 — 그룹·역할 매퍼
- [ ] 10부 운영 — 수명 기본값 · 이벤트 · 메트릭
