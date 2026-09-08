# Keycloak × Active Directory login for a Kubernetes service — deck build plan

Agent-facing plan (for the Opus build session). Language: English here; **all
user-facing output, all deck body text and all source comments are Korean.**
Follow the global `~/.claude/CLAUDE.md` (Korean reports, TDD RED→GREEN, one task =
one commit, ≤12-line `history.md` entry per commit, prepend only) and the repo
`CLAUDE.md` (self-contained deck from `template.html`, Fold 374/768 px, `index.html`
card + `README.md` row, embedded `DeckMono` font, Korean narrative commit messages
without a type prefix — the repo convention overrides the global one here).
This plan is modelled on `boricha/PLAN.md`. **Reuse the `boricha/deck/` tooling** —
`build_deck.py`, `hl.py`, `chunks.py`, `split_ranges.py`, `gen_fonts.py`,
`test_fonts.py`, `untab.py`, `check_deck.js`, `base/`, `extra.css` — copy them into
`keycloak_ad/deck/` and change only title/brand/paths/palette/language maps
(add `yaml`, `sh`, `json`, `http` to `hl.py` if missing; the template highlighter
already knows `yaml`/`http`). `player.js`/`gen_appendix.py` are not needed.

## 0. What the user asked for (do not narrow it)

> "template.html이용해서 k8s에서 돌아가는 서비스에 keycloak으로 ad연동하는걸 쉽게
> 설명해주는 문서를 만들껀데 … 대상은 대학교 4학년이고 웹 개념이 거의 없어.
> 장수는 1000장이하."

| Requirement | Meaning in this plan |
|---|---|
| "k8s에서 돌아가는 서비스에 Keycloak으로 AD 연동" | End-to-end: a web service running in Kubernetes lets people log in with their **company/school Active Directory account**, through **Keycloak** (OIDC provider + LDAP user federation). Cover *why* each piece exists, *how* the pieces talk, *how to set it up*, and *how to debug it*. Not a Keycloak feature tour. |
| "쉽게 설명" / "웹 개념이 거의 없어" | The reader is a 4th-year CS-adjacent student who has written programs but never built a web app. **Parts 1–4 build the prerequisites from zero** (HTTP, cookie, redirect, TLS, container, Pod, directory, LDAP, SSO, token). One new idea per slide, analogy first, then the real thing, then the real bytes. See §5.9. |
| "template.html 이용해서" | Deck assembled on `template.html` via the boricha builder. ←/→ pages, ↑/↓ scroll, gamepad, Fold 374/768, `DeckMono` embedded, single file, no CDN. |
| "1000장 이하" | Hard cap **1000**. Target **760–840**, hard minimum **650**. Count with the builder, never estimate. Depth beats padding: if a part comes in short, do not inflate it. |

## 1. Goal

Deliverables at the end of the last commit:

1. `Keycloak_AD_연동_쉽게_배우기.html` at the repo root — the deck (title:
   "쿠버네티스 서비스에 회사 계정으로 로그인하기 — Keycloak × Active Directory").
2. `keycloak_ad/` — everything the deck quotes: runnable Go programs (stdlib only),
   Kubernetes manifests, Keycloak realm import JSON, scripts, captured outputs under
   `out/`, and the deck builder + sections.
3. `index.html` card (section `🎬 자동화 & CI/CD 🔄`, right after the CI/CD 교재 card)
   and a `README.md` row (same neighbourhood as CI/CD·ArgoCD entries), with the **real**
   slide count.
4. `keycloak_ad/deck/claims.md` — every factual claim → source URL → slide id.

## 2. Non-negotiables

1. **No hand-typed code in slides.** Every code/YAML/JSON/shell block is cut from a real
   file under `keycloak_ad/` by the builder (`<!--CODE file=… lines=A-B-->`). Every
   terminal/output block is a real capture under `keycloak_ad/out/` (`<!--RUN …-->`).
   Coverage: every file listed in §6 must be referenced; files marked `partial` may be
   quoted partially, the rest must be covered line-exactly-once (builder's "오류 N건" = 0).
2. **Evidence tiers — label honestly, on the slide, with a badge:**
   - **A `실행 검증`** — ran on this machine, output captured under `out/`.
   - **B `구문 검증`** — cannot run here (no cluster) but validated by a real tool:
     `kubectl create --dry-run=client`, `kubectl kustomize`, `kubeconform -strict`,
     Keycloak `--import-realm` accepting the JSON (if Keycloak runs, tier A for that).
   - **C `문서 근거`** — neither; quoted from vendor docs with the URL in `claims.md`
     (e.g. the AD-side GPO screenshot text, Entra ID differences). Keep tier C under
     10 % of code-bearing slides and never for anything the reader will copy-paste.
3. **Tests first** for every Go package (RED before GREEN). LDAP BER codec, JWT
   encode/verify, PKCE, OIDC discovery/token handlers are table-driven tests.
4. **Standard library only in Go** (`go.mod` has no `require`). LDAP, JWT (RS256 via
   `crypto/rsa` + `crypto/sha256`), PKCE, OIDC RP and OP are all written by us — that
   is the teaching point ("the protocol is small enough to hold in your hand").
5. Every claim about Keycloak behaviour is checked against the **pinned Keycloak
   version's docs** (`https://www.keycloak.org/docs/<ver>/server_admin/`,
   `…/server_development/`, Server Guides `…/server/all-config`, LDAP federation page)
   and, when Keycloak runs here, against its actual behaviour. Every protocol claim
   against the RFC (6749, 6750, 7636, 7519, 7517, 7009, 7662, 8414, OIDC Core 1.0,
   OIDC Discovery, OIDC RP-Initiated Logout, Back-Channel Logout; LDAP RFC 4511/4513/
   4515/4519; Simple Paged Results RFC 2696). Every AD claim against Microsoft Learn
   (sAMAccountName, userPrincipalName, objectGUID, memberOf, userAccountControl bits,
   Global Catalog ports 3268/3269, LDAP signing/channel binding). Record in `claims.md`.
6. Deck opens offline: no CDN, no web fonts, no external images. Inline SVG only.
   Render each SVG once with `rsvg-convert` and look at it (see memory `svg-render-toolchain`).
7. Korean body text; Korean comments in all sources (explain *why*). Non-trivial
   algorithms (BER length decoding, base64url, RS256 verify) state complexity.
8. Deck HTML is a build artifact. Never edit it by hand. Keep it openable at every commit.
9. Do not modify `boricha/`, `template.html`, `tools/`, other decks. Read/copy only.
10. **Fictional but realistic names, consistently:** AD domain `ad.campus.example`
    (`DC=ad,DC=campus,DC=example`), service account `CN=svc-keycloak,OU=Service Accounts,…`,
    users `minji` (student intern, the protagonist), `prof.kim`, `admin.lee`; groups
    `lunch-users`, `lunch-admins`; Keycloak realm `campus`; client `lunch-web`;
    the service is **학식 예약 (lunch)** at `https://lunch.campus.example`; Keycloak at
    `https://sso.campus.example`. Never use real company names, hosts, or the user's
    employer. Passwords in examples are obviously fake (`Passw0rd!-demo`) and every
    slide that shows one carries the "예제용" badge.
11. Secrets never land in git except demo values clearly marked; the `out/` captures are
    scrubbed of anything token-like longer than 24 chars except the JWTs we mint with
    our own demo key (those are the lesson).

## 3. Environment (verified 2026-09-08 — do not re-discover)

| Tool | Status | Notes |
|---|---|---|
| go 1.27.0 android/arm64 | ok | `GOTOOLCHAIN=local`, build with `-p 1`. This module has no deps → `GOPROXY=off` works. |
| Java 21 (`/usr/bin/java`, OpenJDK 21.0.12) | ok | Enough for Keycloak 26.x dist (`kc.sh`). **One JVM at a time, ever.** |
| node 24 | DOM stub only | `deck/check_deck.js`. Playwright unusable (platform=android) — do not try. |
| python3 3.14 + fontTools + brotli | ok | builder + DeckMono subset. No PyYAML/cryptography/jwt/ldap3 — do not `pip install`; validate YAML with `kubectl`/`kubeconform`, JSON with `python3 -m json.tool`. |
| docker / kind / minikube / k3d / kubectl / helm | **absent** | No cluster is possible here. Download static arm64 binaries into `keycloak_ad/bin/` (git-ignored): `kubectl` from `https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/arm64/kubectl` and `kubeconform` (GitHub release tarball, linux-arm64). Record versions + sha256 in `claims.md`. `kubectl kustomize`, `kubectl create --dry-run=client -f`, `kubectl explain` are offline. `kubectl apply --dry-run=client` **needs a server** — do not use it. |
| Keycloak | downloadable | `https://github.com/keycloak/keycloak/releases/download/<ver>/keycloak-<ver>.zip` (~150 MB). Pick the newest 26.x GA on the day you start; pin it in `keycloak/VERSION` and everywhere in the deck. Unzip under `keycloak_ad/kc/` (git-ignored). |
| network | ok | proxy.golang.org, dl.k8s.io, github.com reachable via `curl`. `jq` is absent → use `python3 -c 'import json,sys;…'`. |
| tmux, curl, openssl, rsvg-convert | ok | `openssl` makes the demo CA + server certs for the LDAPS/HTTPS slides. |
| RAM | **very tight** (~2.2 GB available, swap nearly full) | Rules from memory `android-memory-limits`: at most **2 subagents**, **1 JVM**, one `go build`/`go test` at a time, `free -m` before heavy steps. Keycloak dev mode is allowed **only** when `available ≥ 1800 MB`, with `JAVA_OPTS_KC_HEAP="-Xms128m -Xmx640m"`, nothing else heavy running, and it must be killed right after the capture script finishes. If it cannot start, the Keycloak-run slides become tier B/C — say so on the slide; do not fake output. |

## 4. Repository layout

```
keycloak_ad/
  PLAN.md                    this file (+ progress log at the bottom, newest first)
  go.mod                     module treasure/keycloak_ad, go 1.27, NO require block
  Makefile                   test vet run-web run-ldap run-oidc record validate-k8s kc-fetch kc-run kc-e2e deck deck-check clean
  .gitignore                 bin/ kc/ out/*.tmp
  web/                       Part 1 ladder — one concept per program, stdlib net/http
    01_hello/main.go         a server that answers one URL; shows request line + headers
    02_form_cookie/main.go   login form → Set-Cookie session → protected page → logout
    03_redirect/main.go      302 chains, Location header, "why the browser follows"
    04_tls/main.go           HTTPS with a self-signed cert from certs/ (curl -k vs --cacert)
  ldap/                      Part 3 — LDAP we can see
    ber/ber.go               BER TLV encode/decode subset (INTEGER, OCTET STRING, SEQUENCE, SET, ENUM, application/context tags)  O(n)
    ber/ber_test.go
    proto/proto.go           LDAPMessage, BindRequest/Response, SearchRequest/ResultEntry/ResultDone, UnbindRequest, Filter AST, Simple Paged Results control (1.2.840.113556.1.4.319)
    proto/proto_test.go      golden bytes for bind/search/filters (incl. the exact filters Keycloak sends)
    fakead/                  a tiny "AD": in-memory directory with AD attribute names
      main.go                flags: -addr :10389 -ldaps :10636 -cert certs/ldap.crt -key certs/ldap.key -dir data/campus.ldif -log out/fakead.log
      dir.go                 LDIF loader, DN normalisation (case-insensitive), objectGUID as 16 raw bytes, memberOf as computed attribute, userAccountControl, pwdLastSet, lockout after 5 bad binds (AD default policy analogue)
      server.go              accept loop, per-conn message loop, bind (simple; service account + user password check), search (base/one/sub scope, filter eval, attribute selection, paged control echo), unbind, LDAPS via crypto/tls
      *_test.go
    ldapcli/main.go          `ldapcli bind|search|whoami` — prints the request bytes annotated + the parsed reply; used for every Part 3 and Part 7 capture
  oidc/                      Part 4 — OIDC we can see
    jwt/jwt.go               base64url, JWS compact, RS256 sign/verify (crypto/rsa PKCS1v15 + SHA-256), claims struct, exp/nbf/iss/aud checks, JWKS (n/e ↔ *rsa.PublicKey)
    jwt/jwt_test.go          RFC 7515/7519 vectors + tamper tests (changed payload, wrong key, alg=none rejected)
    pkce/pkce.go             verifier/challenge S256 (RFC 7636 appendix B vector in tests)
    miniidp/main.go          the OP: /.well-known/openid-configuration, /authorize (login form), /token (code + PKCE + client_secret), /jwks, /userinfo, /logout; users come from fakead (bind-as-user) — this is "Keycloak in 400 lines"
    miniapp/main.go          the RP: /login → state+nonce+PKCE → redirect; /callback → token → verify id_token via JWKS → session cookie; /me; /logout (RP-initiated); role check from `groups` claim
    jwtool/main.go           `jwtool decode|verify -jwks URL` — used in captures to show tokens minted by miniidp AND by real Keycloak
  k8s/                       Parts 6, 8, 9 — what the reader applies to a real cluster
    base/namespace.yaml  postgres.yaml (StatefulSet+Service+Secret)  keycloak.yaml (Deployment+Service+ConfigMap env)  keycloak-ingress.yaml
         lunch-app.yaml (Deployment+Service)  lunch-ingress.yaml  oauth2-proxy.yaml (Deployment+Service+Secret+ConfigMap)  lunch-ingress-authreq.yaml (ingress-nginx auth_request variant)
         ad-truststore.yaml (Secret with the AD CA)  networkpolicy.yaml  kustomization.yaml
    overlays/dev/  overlays/prod/   (replicas, hostnames, resources, KC_PROXY_HEADERS, hostname-strict)
    validate.sh              kubectl kustomize each overlay → kubectl create --dry-run=client → kubeconform -strict -summary; writes out/k8s_validate.txt
  keycloak/
    VERSION                  pinned version string
    realm-campus.json        realm export: realm settings, client lunch-web (confidential, PKCE S256 required), client scopes + mappers (groups → `groups` claim, sAMAccountName → preferred_username), LDAP user federation pointing at fakead (vendor "Active Directory", READ_ONLY, objectGUID, sAMAccountName, pagination on, sync settings), LDAP mappers (username, first/last name, email, MSAD user account control, group-ldap-mapper), roles lunch-user/lunch-admin, group→role mapping
    fetch.sh                 download + sha256 + unzip into ../kc (idempotent)
    run_dev.sh               free-memory guard → kc.sh start-dev --import-realm --http-port 8080 with heap caps; waits for /health/ready; writes pid
    e2e_login.sh             curl+python3: discovery → authorize → login form POST (cookie jar) → 302 code → token → jwtool verify → userinfo → logout; every step's request/response saved to out/kc_e2e_NN.txt
    admin_api.sh             admin token → GET realm, user federation component, trigger "sync all users", list users, search minji — shows what the console buttons really call
    stop.sh
  certs/                     make_certs.sh (openssl: demo CA, ldap.ad.campus.example, sso.campus.example) — generated, committed (demo only, obviously fake, 10-year expiry noted)
  data/campus.ldif           the fake AD content: OUs, 6 users, 3 groups, 1 service account
  tools/record.sh            drives every tier-A capture in order; each capture is one file under out/; run twice, md5 must match (timestamps/tokens are normalised by tools/scrub.py)
  tools/scrub.py             normalises dates, random state/nonce, jti in captures
  out/                       committed captures the deck quotes
  deck/                      build_deck.py hl.py chunks.py split_ranges.py gen_fonts.py test_fonts.py untab.py check_deck.js base/ extra.css sections/ claims.md
```

## 5. Design decisions (decided — do not re-litigate; record deviations in the log)

### 5.1 The whole system, drawn once, grown part by part
One SVG (`deck/base/system.svg` fragments): 브라우저 · 학식 예약 앱(Pod) · Ingress ·
Keycloak(Pod) · Postgres · AD(도메인 컨트롤러). Each part "lights up" the boxes it
adds. Every part's first slide and last slide show the current state of this picture.
Same colours everywhere: browser blue, app green, Keycloak purple (`--special`), AD amber,
network arrows grey, **token/cookie/credential as three distinct icons** (열쇠 = password,
카드키 = token, 손목밴드 = cookie/session) — the metaphor is fixed in Part 4 and reused.

### 5.2 Three sessions, named and coloured
The single most common confusion. Name them once and keep the names: **A. 브라우저↔Keycloak
세션** (KEYCLOAK_IDENTITY cookie, SSO), **B. 브라우저↔앱 세션** (the app's own cookie), **C.
앱↔Keycloak 토큰** (ID/access/refresh). Logout, timeouts and "why am I still logged in?"
are all explained on this triangle.

### 5.3 We build a miniature first, then meet the real thing
Part 3: `fakead` before AD. Part 4: `miniidp`+`miniapp` before Keycloak. Part 7: Keycloak
talks to `fakead`, so the reader sees the *actual* LDAP searches Keycloak issues (from
`out/fakead.log`) instead of trusting a diagram. Part 8: the real app uses the same RP code
as `miniapp`. Each "real thing" slide has a "나란히 보기" comparing our 400 lines with the
product's equivalent knob.

### 5.4 `fakead` fidelity — exactly what Keycloak's AD provider needs, no more
Simple bind (service account DN + user DN), `whoami` not needed, search scopes
base/one/sub, filters `=`, `&`, `|`, `!`, presence, `objectClass=*`; attributes returned
as requested; `objectGUID` **binary** (Keycloak's "UUID LDAP attribute" for AD expects
the 16-byte form — say so on the slide); `memberOf` and `member`; `sAMAccountName`,
`userPrincipalName`, `cn`, `sn`, `givenName`, `mail`, `distinguishedName`,
`userAccountControl` (512 normal, 514 disabled, 66048 password-never-expires),
`pwdLastSet`; Simple Paged Results control accepted and answered with an empty cookie
(single page). Bind errors use AD's `data 52e` (bad password) / `data 533` (disabled) /
`data 775` (locked) diagnostic strings in the `diagnosticMessage` so the deck can teach
how to read them. Lockout after 5 wrong binds within 10 minutes. LDAPS on 10636 with our
demo CA — the truststore lesson. **Not** implemented (and one slide says so): StartTLS,
SASL/GSSAPI/Kerberos, modify/add/delete, referrals, Global Catalog port 3268 (explained,
not emulated).

### 5.5 `miniidp` + `miniapp` — the flow in stdlib
Authorization Code + PKCE(S256) + `state` + `nonce`; ID token RS256 with a key generated
at start (2048-bit; `-key` flag to reuse for reproducible captures); JWKS with `kid`;
`/userinfo` from fakead attributes; `groups` claim from `memberOf`; refresh token
rotation; RP-initiated logout with `id_token_hint` + `post_logout_redirect_uri`.
Deliberately **omitted** with a slide each: implicit/hybrid flows (why they are gone),
client credentials (mention only; link 웹_인증 ch19), device flow, token introspection.

### 5.6 Kubernetes shape — plain manifests + Kustomize, Operator and Helm explained
The reader's cluster is unknown, so the deck ships **plain manifests + Kustomize overlays**
(validated here) as the primary path, and spends 1–2 slides each on the Keycloak Operator
(CRD `Keycloak`, `KeycloakRealmImport`) and the Bitnami/codecentric Helm charts as
"same knobs, different wrapper". Postgres as a StatefulSet for the lesson, with a slide
that says "in production use a managed DB". Keycloak runs in **production mode**
(`kc.sh start --optimized` after `kc.sh build` in the image) behind Ingress TLS
termination with `KC_PROXY_HEADERS=xforwarded`, `KC_HOSTNAME=https://sso.campus.example`,
`KC_HTTP_ENABLED=true` inside the cluster, health on the management port (9000)
readiness `/health/ready`, liveness `/health/live`, metrics `/metrics`. Rolling update
notes: Infinispan cache with `KC_CACHE=ispn` + `KC_CACHE_STACK=kubernetes` +
`jgroups.dns.query` headless service (why two replicas need this), sticky sessions not
required with OIDC. Resource requests/limits from the docs' sizing guide.

### 5.7 App integration — three roads, one recommended
**Road 1 (recommended for a first service): sidecar/gateway with oauth2-proxy** — no app
code change, `--provider=oidc`, `--oidc-issuer-url`, `--allowed-group`, headers
`X-Auth-Request-User/-Email/-Groups` → app trusts headers only from the proxy (network
policy slide). **Road 2: the app speaks OIDC itself** — our Go RP (`miniapp` code reused
as the lunch app), when you need per-user tokens or fine-grained roles. **Road 3: API
gateway / service mesh (Istio RequestAuthentication + AuthorizationPolicy)** — concept
slides only (tier C). Also one slide each: Spring Security / Django / Express one-liner
config, quoted from vendor docs (tier C), so readers on other stacks know the knob names.

### 5.8 Authorization — from AD group to app permission, one straight line
`memberOf: CN=lunch-admins,…` → Keycloak group (group-ldap-mapper, `preserve group
inheritance`, `membership LDAP attribute = member`, `user roles retrieve strategy =
LOAD_ROLES_BY_MEMBER_ATTRIBUTE` for AD) → group→realm role `lunch-admin` → client scope
mapper puts `groups`/`realm_access.roles` into the token → app checks the claim. Show the
same user's token before and after joining the group (two real captures). Least privilege
slide: don't ship all 300 AD groups in the token (`Full group path` off, group filter).

### 5.9 Deck pedagogy (beginner contract — the user's core ask)
- **One new idea per slide.** A slide introduces at most one term; the term gets a
  `<div class="key">` 용어 카드 with 한국어 풀이 + 영문 + 한 줄 비유, and is added to
  the glossary (Part 12) with the slide id.
- **Analogy → picture → real bytes**, in that order, for every protocol concept.
  Analogies fixed for the whole deck: 기숙사 출입 (HTTP 요청/응답), 손목밴드 (쿠키),
  호텔 카드키 (토큰: 프런트=Keycloak, 방=서비스, 신분증=AD 계정), 학교 학적부 (AD/LDAP),
  통역사 (Keycloak between AD's LDAP and the app's OIDC), 아파트 단지 (k8s: 단지=클러스터,
  동=노드, 호=Pod, 경비실=Ingress).
- **Every acronym expanded on first use**, Korean first: "인증(認證, authentication —
  네가 누구인지 확인)" vs "인가(認可, authorization — 무엇을 해도 되는지)". The 인증/인가
  pair gets its own slide and a recurring margin badge.
- **Recurring protagonist**: 민지, 4학년 인턴, 학교 IT팀. Each part opens with 민지's
  problem of the day ("학식 예약 앱에 왜 또 회원가입을 해야 하지?") and closes with her
  one-paragraph 회고 (what she can now explain to a friend).
- **Every part ends with**: 3–5 quiz slides (`.quiz`), a "실수 박물관" slide (the errors a
  beginner will hit, with the exact error text captured), and the grown system picture.
- **Every command is copy-paste-able and shown with its output** (tier A) or its
  validator's output (tier B). No "…" elided output unless the elision is marked `(중략)`.
- **Never assume**: prior slides are the only prerequisite. If a slide needs JSON, DNS,
  base64, hashing, public-key signatures, or YAML indentation, there is a slide for it
  earlier (Part 1 has a "도구 상자" chapter: JSON, base64/base64url, 해시, 공개키 서명,
  YAML — each with an in-browser demo).
- **In-browser demos** (template `__demo`): HTTP 요청 조립기, 쿠키 시뮬레이터(만료·경로),
  리다이렉트 체인 애니메이션, base64url 인코더, JWT 디코더(3부분 색칠), PKCE 계산기
  (Web Crypto SHA-256), LDAP 필터 해석기, DN 조립기, 토큰 만료 타임라인, "세 세션"
  로그아웃 시뮬레이터, YAML 들여쓰기 검사기, k8s 라벨 셀렉터 매칭기. Each demo is
  tested by `check_deck.js` (DOM stub) at least for "runs without throwing".
- **Cross-links instead of duplication**: depth on OAuth2/OIDC/SAML/JWT →
  `./웹_인증_완전_가이드.html#ch10/#ch12/#ch13/#ch14/#ch16`; k8s objects and Argo CD →
  `./CICD_GitOps_실전_교재.html#ch9/#ch10/#ch12`; cookies → `./쿠키_쉽게_배우기.html`.
  This deck still explains each of these at beginner depth; the links are for "더 깊이".
- **Fold rule**: no `<pre>` line over 72 columns (builder check), tables in `.tblwrap`,
  `.g2/.g3` only for short content, no box-drawing characters, SVG `viewBox` with
  `width:100%`, text in SVG ≥ 12 px at 374 px.

### 5.10 What we deliberately leave out (one "이 덱이 다루지 않는 것" slide)
Kerberos/SPNEGO desktop SSO (concept slide + link only), SAML (Keycloak can, link 웹_인증
ch16), Entra ID / Azure AD (one comparison slide: it is OIDC itself, Keycloak becomes an
identity broker), Keycloak Authorization Services (UMA), custom SPIs/themes beyond a
login-page logo, multi-realm federation, HA across clusters.

## 6. Coverage file set

Line-exactly-once: everything under `web/`, `ldap/`, `oidc/` (`*.go`, not `_test.go` —
tests are quoted partially with `partial`), `k8s/**/*.yaml`, `keycloak/realm-campus.json`,
`keycloak/*.sh`, `certs/make_certs.sh`, `data/campus.ldif`, `Makefile`, `go.mod`.
Partial: `*_test.go`, `tools/*`, `out/*` (quoted by `RUN`, not coverage).
Not quoted: `deck/*`, `bin/*`, `kc/*`.

## 7. Deck outline (section → target slides; total ≈ 800)

| # | Section file | Part | Target | What the reader can do afterwards |
|---|---|---|---|---|
| 0 | `00_start.html` | 표지 · 읽는 법 · 등장인물 · 전체 그림 · 이 덱이 다루지 않는 것 | 12 | Know the six boxes and the three sessions exist. |
| 1 | `01_web.html` | 1부 웹이 돌아가는 법: URL·DNS·HTTP 요청/응답·상태코드·리다이렉트·폼·쿠키·세션·TLS/HTTPS·도구 상자(JSON·base64url·해시·서명·YAML) | 80 | Read a `curl -v` transcript; explain why a cookie logs you in. Ladder `web/01–04`. |
| 2 | `02_k8s.html` | 2부 컨테이너와 쿠버네티스 최소한: 프로세스→이미지→컨테이너→Pod→Deployment→Service→Ingress→ConfigMap/Secret→Namespace→라벨·셀렉터→헬스체크·리소스→kubectl 읽기 | 65 | Read a manifest and say what it creates. Tier B validation shown. |
| 3 | `03_ad.html` | 3부 회사 계정의 세계: 디렉터리·도메인·DN·OU·사용자 속성(sAMAccountName·UPN·objectGUID)·그룹·memberOf·LDAP bind/search·필터·LDAPS·서비스 계정·비밀번호 정책/잠금·포트(389/636/3268)·Kerberos는 무엇인가(개념) | 75 | Run `ldapcli` against `fakead`, read the bytes, write a filter. |
| 4 | `04_sso.html` | 4부 인증 위임의 원리: 앱마다 비밀번호를 받으면 안 되는 이유·SSO·OAuth2 역할·인가 코드 흐름·PKCE·state/nonce·ID/액세스/리프레시 토큰·JWT 구조·서명·JWKS·클레임·세 세션·로그아웃 | 95 | Run `miniidp`+`miniapp`, decode a token with `jwtool`, explain each redirect. |
| 5 | `05_keycloak.html` | 5부 Keycloak 이란: realm·client·user·group·role·client scope·mapper·user federation·identity broker·관리 콘솔 지도·dev vs prod 모드·설정 3경로(env/CLI/conf)·admin REST API·realm export/import | 65 | Navigate the console; import `realm-campus.json`; call the admin API. |
| 6 | `06_k8s_keycloak.html` | 6부 Keycloak을 k8s에 올리기: 배포 선택지(매니페스트/Operator/Helm)·Postgres·Secret·이미지 빌드(`kc.sh build`)·hostname·프록시 헤더·Ingress+TLS·health/metrics·리소스·2개 이상 replica(ispn)·롤링 업데이트·백업·업그레이드 | 75 | Apply the overlay to a real cluster and know each env var's purpose. |
| 7 | `07_ad_federation.html` | 7부 AD 연동: User Federation LDAP 설정 필드 하나하나·vendor=AD가 바꾸는 기본값·READ_ONLY vs WRITABLE vs UNSYNCED·objectGUID·sAMAccountName vs UPN 로그인·서비스 계정 권한·truststore(자체 CA)·동기화(주기/변경분)·매퍼 6종·MSAD user account control·잠금/비활성 계정 동작·Keycloak이 실제로 보내는 LDAP 검색(fakead 로그)·문제 15가지 진단 순서 | 95 | Configure federation against a real AD from the field table; read the LDAP log to debug. |
| 8 | `08_app.html` | 8부 서비스에 로그인 붙이기: 세 갈래 길·oauth2-proxy(사이드카/ingress auth_request)·헤더 신뢰 경계·앱이 직접 OIDC(우리 RP 코드 → lunch app)·리다이렉트 URI 규칙·세션 쿠키 설정·로그아웃 3종·다른 스택 한 줄(Spring/Django/Express)·게이트웨이/메시(개념) | 100 | Put a login in front of any service in the cluster two ways. |
| 9 | `09_authz.html` | 9부 권한: AD 그룹→Keycloak 그룹→역할→토큰 클레임→앱 검사·클라이언트 스코프·최소권한·관리자 화면 보호·같은 사용자의 전/후 토큰 | 50 | Give `lunch-admins` the admin page and nobody else. |
| 10 | `10_ops.html` | 10부 운영과 보안: 토큰·세션 수명 표·키 회전·시크릿 관리(Secret/외부 시크릿)·감사 이벤트·모니터링(/metrics)·로그 읽기·백채널 로그아웃·업그레이드 순서·장애 시나리오 10개(증상→원인→명령) | 60 | Run it for a semester without paging the professor. |
| 11 | `11_walkthrough.html` | 11부 처음부터 끝까지 한 번에: 체크리스트 40단계, 각 단계 = 명령 + 기대 출력 + 실패 시 볼 곳 | 40 | Do the whole thing on a fresh cluster in an afternoon. |
| 12 | `12_wrap.html` | 12부 마무리: 요약 그림 · 용어집(≈60) · 치트시트(kubectl/kcadm/curl/ldapcli) · FAQ 15 · 더 읽을 것 · 출처 | 35 | — |
| | | **Total** | **≈ 847** | Trim toward 780–840; hard cap 1000. |

## 8. Work order = commit plan (one task, one commit; verify before each)

Each step: RED tests → GREEN → `make test` → captures → sections → `make deck` (오류 0건)
→ `make deck-check` → `python3 tools/embed_mono_font.py --check` → `history.md` entry
(≤12 lines) → Korean commit message → append to the progress log below → `free -m`.

1. **Skeleton.** Copy boricha deck tooling into `keycloak_ad/deck/`, retarget paths/title/
   brand/palette (palette: navy `--accent` from template kept, `--special` purple = Keycloak,
   add `--ad: #b7791f` amber and `--app: #2e7d32` green as CSS vars used by SVGs), `go.mod`,
   `Makefile`, `.gitignore`, `00_start.html` (12), placeholder section files for 1–12 so
   the deck opens with part covers. `deck/claims.md` header. `certs/make_certs.sh` + certs.
   Commit: `Keycloak×AD 덱 뼈대 — 빌더·표지·부 표지 12개`.
2. **Part 1 web ladder** (`web/01–04` with tests, captures via `curl -v` and `tools/record.sh`;
   in-browser demos for cookie/redirect/base64url/JSON/YAML). Section `01_web.html`.
3. **LDAP core** (`ldap/ber`, `ldap/proto`, `fakead`, `ldapcli`, `data/campus.ldif`;
   golden-byte tests; LDAPS). Captures: bind ok / 52e / 775, search with paging, filter
   variants, raw-bytes annotation. Section `03_ad.html`.
4. **Part 2 k8s minimum** — download `kubectl`+`kubeconform` to `bin/` (versions to claims),
   first manifests for the lunch app only, `validate.sh`, captures of `kubectl explain`,
   dry-run, kubeconform. Section `02_k8s.html`.
5. **OIDC core** (`oidc/jwt`, `oidc/pkce`, `miniidp`, `miniapp`, `jwtool`; tests incl. RFC
   vectors and tamper cases). Captures: full flow via curl cookie-jar, decoded tokens,
   JWKS, failed nonce/state, expired token. Section `04_sso.html`.
6. **Keycloak fetch + run + e2e** — `keycloak/VERSION`, `fetch.sh`, `realm-campus.json`,
   `run_dev.sh` (memory guard), `e2e_login.sh`, `admin_api.sh`, `stop.sh`. Run once with
   fakead up: capture discovery, login page, token, userinfo, admin API, **fakead.log of
   the searches Keycloak made**, sync-all-users result, disabled/locked user attempts,
   before/after group tokens. If Keycloak cannot start (memory), record the attempt's
   `free -m` and the error in `out/kc_unavailable.txt` and proceed with tier C for those
   slides. Sections `05_keycloak.html`, `07_ad_federation.html` (first half).
7. **k8s for Keycloak** — `k8s/base/postgres.yaml keycloak.yaml keycloak-ingress.yaml
   ad-truststore.yaml networkpolicy.yaml`, overlays, validation captures. Section `06_k8s_keycloak.html`.
8. **Part 7 second half** — field-by-field table, mappers, troubleshooting 15, sync.
9. **Part 8 app roads** — `oauth2-proxy.yaml`, `lunch-ingress-authreq.yaml`, lunch app =
   `miniapp` reused with `-issuer` flag pointing at Keycloak (captured against local
   Keycloak if available, else against miniidp with a slide saying "same code, issuer
   swapped"). Section `08_app.html`.
10. **Part 9 authz** — group mapper config, role mapping, two-token comparison. `09_authz.html`.
11. **Part 10 ops** + **Part 11 walkthrough** — `10_ops.html`, `11_walkthrough.html`.
12. **Part 12 wrap** — glossary generated from the 용어 카드 slides by a small script
    (`deck/gen_glossary.py`, reads `data-term` attributes), cheat sheet, FAQ, sources.
13. **Publish** — final count from the builder, `index.html` card, `README.md` row, font
    embed, `--check`, `check_deck.js`, SVG render pass. Commit:
    `Keycloak×AD 연동 쉽게 배우기 — 덱 N장 공개, index·README 카드 함께`.
14. **Review pass** (separate commits, counted by kind per repo convention): fact check
    every claim against `claims.md`, 374/768 overflow heuristics, quiz answers, cross-links
    resolve (`grep -o 'href="\./[^"]*#[^"]*"'` → ids exist in target decks), no orphan
    용어 카드, slide count in card/README matches.

Subagents: at most 2 in parallel, and only for disjoint sections (e.g. steps 2 and 3
together, 7 and 8 together). Never two Go builds at once; never a subagent while Keycloak
is running. The orchestrator writes shared material once (names in §2.10, colours in §5.1,
analogies in §5.9) and hands it in the prompt.

## 9. Verification checklist (before calling any step done)

- `make test` green, `go vet ./...` clean (run serially, `-p 1`).
- `make record` twice → identical md5 of `out/` (after `scrub.py`).
- `make validate-k8s` → kubeconform summary shows 0 invalid, 0 errors; captured.
- `make deck` → "오류 0건" (coverage, `<pre>` ≤ 45 lines and ≤ 72 columns, `<li>` ≤ 14
  per slide, every `<!--CODE-->` resolved, every `RUN` file exists, no box-drawing chars).
- `make deck-check` (node DOM stub: slide count, TOC ids unique, every `data-demo` wired,
  every quiz has an answer, all `href="./…#id"` cross-links resolve in the target file).
- `python3 tools/embed_mono_font.py 덱.html` then `--check` passes.
- Every SVG rendered with `rsvg-convert` once and eyeballed at 374 px width.
- Every tier badge present on every code/output slide; tier C ≤ 10 % of them.
- `claims.md`: every slide id that states a version, port, default value, RFC section or
  AD attribute semantics has a line.
- Slide count in `index.html` card and `README.md` equals the builder's count.
- No real hostnames/companies/emails; grep for `samsung`, `@`, `corp`, the user's name.
- `history.md` entry ≤ 12 lines, prepended; commit message Korean, no type prefix.

## 10. Decisions confirmed by the user (2026-09-08 — all defaults accepted; do not re-ask)

1. Deck filename: **`Keycloak_AD_연동_쉽게_배우기.html`** (matches the `…_쉽게_배우기` series).
2. Keycloak version: **newest 26.x GA on start day, pinned** in `keycloak/VERSION`.
3. Ingress flavour for the concrete YAML: **ingress-nginx** (auth_request path shown); others get one comparison slide.
4. AD flavour: **on-prem AD over LDAPS with a service account**; Entra ID is a one-slide comparison.
5. Primary integration road: **oauth2-proxy first, then app-side OIDC in Go**; Spring/Django/Express one slide each (tier C).
6. Running real Keycloak here is memory-gated (§3). If it fails: **ship tier C for those slides and say so** (`out/kc_unavailable.txt` records the attempt).
7. Target length: **≈ 800** (760–840), hard cap 1000, hard minimum 650.

## Progress log (newest first)

_(empty — the Opus session appends here after every commit: 기획/TC/개발/검증/비고, Korean, ≤ 12 lines)_
