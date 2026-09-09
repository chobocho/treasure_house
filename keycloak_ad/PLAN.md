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
| "1000장 이하" → **2000 (2026-09-08 사용자가 올림)** | Hard cap **2000**. The §7 per-part targets stand as reference points; overrunning them is allowed when one-idea-per-slide requires it (Part 1 came in at 104 vs 80). Count with the builder, never estimate. Depth beats padding: if a part comes in short, do not inflate it. |

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
7. Target length: ~~≈ 800 (760–840), hard cap 1000~~ → **hard cap 2000, no fixed target**
   (changed by the user on 2026-09-08, after Part 1 landed at 104 slides against a target of 80).
   Hard minimum 650 stands. Per-part §7 targets remain as reference points, and the builder
   prints actual vs target plus the projected total on every build.

## Progress log (newest first)

### [2026-09-09 01:50] 10단계 9부 — 권한, 36장 (누적 914장)

- **기획:** 6개 장 — 한 줄로 이어지는 길(다섯 걸음) · 같은 사람의 전과 후 ·
  그룹인가 역할인가 · 앱마다 다르게 싣기 · 최소 권한 · 관리자 화면 두 겹.
  퀴즈 2.
- **개발:** `keycloak/authz_lab.sh`(신규, 실험 2) · `tools/record.sh` ·
  `deck/sections/09_authz.html`(신규) · `13_appendix.html`(FULLSRC +1) ·
  `deck/claims.md`(9부 10행)
- **잡은 것:** 처음에 "역할은 매퍼를 안 붙여도 실린다" 고 썼는데,
  캡처를 떠 보니 **ID 토큰에는 없었다**. 기본 client scope 인 `roles` 는
  **액세스 토큰에만** 싣는다. 실험을 고쳐 같은 사람의 두 토큰을 나란히
  뜨게 했고, 그 함정 자체를 3장의 경고로 만들었다.
- **증거 둘:** 유나를 그룹에 넣기 전(505바이트) → 후(519바이트)의 두 토큰,
  그리고 그룹에 역할을 매어 소희에게만 `lunch-admin` 이 붙는 액세스 토큰.
- **검증:** 914장 · **커버리지 8801/8801줄 100퍼센트** · 조립 0건 ·
  역검증 통과 · deck-check 0건(퀴즈 54 · 데모 12) · 글꼴 통과 · test 14패키지.
- **다음:** §8 11단계(10·11부 — 운영, 전체 훑기).

### [2026-09-09 01:10] 9단계 8부 — 서비스에 로그인 붙이기, 41장 (누적 878장)

- **기획:** 7개 장 — 세 갈래 길 · 길 1(oauth2-proxy) · 헤더를 믿는다는 것 ·
  길 2(앱이 직접) · **약속을 갚는다** · 로그아웃 세 종류 · 다른 스택. 퀴즈 4.
- **이 부의 증거:** `keycloak/app_e2e.sh` 가 4부의 실행 파일(`bin/miniapp`)을
  **다시 빌드하지 않고** `-issuer` 만 진짜 Keycloak 으로 바꿔 띄운다.
  로그인이 통과하고, AD 에서 온 이름과 그룹이 화면에 찍히고,
  minji 는 403 · admin.lee 는 200 을 받는다. 4부 6장에서 한 약속이 그대로 갚아졌다.
- **개발:** `keycloak/app_e2e.sh`(신규) · `k8s/base/oauth2-proxy.yaml`(신규) ·
  `k8s/base/lunch-ingress-authreq.yaml`(신규) · `kustomization`(16 → 20 오브젝트) ·
  `tools/record.sh` · `deck/sections/08_app.html`(신규) ·
  `13_appendix.html`(FULLSRC +3) · `deck/claims.md`(8부 15행)
- **경계선 하나를 크게 다뤘다:** 헤더를 믿는 구조는 **담장이 없으면 아무것도
  안 지킨다**. 클러스터 안 아무 Pod 나 `X-Auth-Request-User` 를 적어 보낼 수 있다.
  그 퀴즈를 3장 끝에 뒀고, 길 2가 더 안전한 이유로 이었다.
- **검증:** 878장 · **커버리지 8612/8612줄 100퍼센트** · 조립 0건 ·
  역검증 통과 · deck-check 0건(퀴즈 52 · 데모 12) · 글꼴 통과 ·
  `sh k8s/validate.sh` 세 벌 각 20개 오브젝트 통과 · test 14패키지.
- **다음:** §8 10단계(9부 권한 — 그룹에서 역할로, 토큰 크기).

### [2026-09-09 00:10] 8단계 7부 후반 — 26장 (7부 75장, 누적 829장)

- **기획:** 4개 장 — 설정 칸 전수 표(연결·인증·사람 찾기·동기화) ·
  매퍼를 하나씩(여섯 종) · 동기화(전체와 변경분) · 진단 열다섯. 퀴즈 3.
- **개발:** `keycloak/ad_lab.sh` 실험 둘 추가(매퍼 목록 · 전체 대 변경분
  동기화) · `deck/sections/07_ad_federation.html` · `deck/claims.md`(7행)
- **캡처가 보여 준 것:**
  vendor 를 AD 로 고르면 매퍼가 **아홉 개** 붙는다(우리가 더한 것은 둘).
  변경분 동기화는 `whenCreated>=…`·`whenChanged>=…` 로 **시각을 잘라** 묻는다 —
  1장에서 Keycloak 이 그 두 속성을 달라고 한 이유가 여기서 드러난다.
  그리고 그 필터에는 **삭제를 볼 수단이 없다** — 퇴사자가 남는 이유다.
- **진단 15가지**는 증상을 셋으로 나눴다 — 전원이 못 들어옴(1~5) ·
  일부만(6~10) · 들어오는데 이상함(11~15). 좁혀 가는 순서도 함께 뒀다.
- **검증:** 829장 · **커버리지 8344/8344줄 100퍼센트** · 조립 0건 ·
  역검증 통과 · deck-check 0건(퀴즈 48 · 데모 12) · 글꼴 통과 · test 14패키지.
- **7부 완료.** 75/95장 — 목표보다 적지만 다룰 것은 다 다뤘다.
- **다음:** §8 9단계(8부 — 앱을 붙이는 세 가지 길).

### [2026-09-08 23:30] 7단계 6부 — 쿠버네티스에 Keycloak, 47장 (누적 802장)

- **기획:** 6개 장 — 창고(PostgreSQL StatefulSet) · Keycloak 얹기 ·
  바깥으로 내놓기 · 여러 벌 · 인증서와 담장 · 다른 포장과 마무리. 퀴즈 4.
- **개발:** `k8s/base/{postgres,keycloak,keycloak-ingress,networkpolicy}.yaml` ·
  `k8s/base/kustomization.yaml`(오브젝트 5 → 16) · overlays 둘 ·
  `certs/make_certs.sh`(CA 를 k8s/base 로 복사) · `tools/pickobj.py`(신규) ·
  `tools/record.sh` · `deck/sections/06_k8s_keycloak.html`(신규) ·
  `13_appendix.html`(FULLSRC +4) · `deck/claims.md`(6부 16행)
- **설정:** 운영 모드(`start --optimized`) · `KC_PROXY_HEADERS=xforwarded` ·
  `KC_HTTP_ENABLED=true` · 관리 포트 9000 에 프로브 셋(startup 포함) ·
  `KC_CACHE=ispn`+`kubernetes` 스택과 헤드리스 Service ·
  읽기 전용 루트 · truststore Secret · NetworkPolicy 둘.
- **부딪힌 것 둘:**
  1. YAML 의 접기(`>-`)로 나눈 DNS 이름에 **공백이 끼어** 깨졌다.
     직접 넣어 보고 확인한 뒤 ConfigMap 한 줄로 옮겼다.
  2. **kustomize 는 kustomization 루트 밖의 파일을 못 읽는다**
     (`security; file … is not in or below …`). 일부러 그런 것이라,
     `make certs` 가 CA 를 `k8s/base/ad-ca.crt` 로 한 벌 복사하게 했다.
- **검증:** 802장 · **커버리지 8297/8297줄 100퍼센트** · 조립 0건 ·
  역검증 통과 · deck-check 0건(퀴즈 45 · 데모 12) · 글꼴 통과 ·
  `sh k8s/validate.sh` 세 벌 각 16개 오브젝트 통과 · test 14패키지.
- **다음:** §8 8단계(7부 후반 — 설정 칸 전수 표 · 진단 15 · 동기화 · 매퍼 6종).

### [2026-09-08 18:10] 6단계(3/3) 7부 전반 — 49장 (누적 742장)

- **기획:** 7개 장 — 붙이기 전에 정할 것 · 로그인 한 번에 무슨 일이 ·
  무엇으로 로그인하는가 · 서비스 계정과 검색 범위 · LDAPS 와 자체 CA ·
  그룹이 건너오는 길 · 계정 상태 매퍼. 퀴즈 4.
  후반(설정 칸 전수 표 · 진단 15 · 동기화 · 매퍼 6종)은 §8 8단계로 남긴다.
- **개발:** `keycloak/ad_lab.sh`(신규, 실험 4종) ·
  `deck/sections/07_ad_federation.html`(신규) · `13_appendix.html`(FULLSRC +1) ·
  `deck/claims.md`(7부 전반 18행) · `tools/record.sh`
- **이 부의 방법:** 설정을 바꿔 가며 **가짜 AD 로그가 어떻게 달라지는지**를
  캡처로 보인다. 그림이 아니라 오간 질의다. 실험 넷 —
  로그인 세 가지(맞음·틀림·꺼진 계정·없는 사람) · 그룹 · 검색 필터 ·
  로그인 아이디를 UPN 으로.
- **찾아 고친 것 셋:**
  1. 실험들이 **서로 상태를 남겨** 답이 어긋났다. "sAMAccountName 으로는
     못 들어간다" 고 적어 둔 화면에 성공이 찍혔다. 실험마다 설정을 되돌리고
     **가져온 사본을 지우도록**(`remove-imported-users`) 고쳤다.
  2. 설정에서 키를 빼는 것만으로는 안 지워진다 — 관리 API 의 PUT 이
     합치기 때문이다. 빈 값으로 덮어써야 없어진다.
  3. 마무리 문구가 사실과 달랐다. 필터를 걸면 사람 목록이 **곧바로** 줄어든다
     (7명 → 6명). 목록은 캐시가 아니라 그때그때 AD 에 묻기 때문이다.
     짐작으로 적었다가 캡처를 보고 고쳤다.
- **id 충돌:** 7부 슬라이드를 `ad-` 로 시작했더니 3부와 통째로 겹쳤다.
  조립기가 잡았고 `f7-` 로 바꿨다.
- **검증:** 742장 · **커버리지 7829/7829줄 100퍼센트** · 조립 0건 ·
  역검증 통과 · deck-check 0건(퀴즈 41 · 데모 12) · 글꼴 통과 · test 14패키지.
- **다음:** §8 7단계(6부 — Keycloak 을 쿠버네티스에 올리기).

### [2026-09-08 17:20] 6단계(2/3) 5부 본문 — 74장 (누적 687장)

- **기획:** 11개 장 — 400줄과 제품 사이 · 띄우기(dev/prod) · 설정 세 경로 ·
  realm · client · user/group/role · client scope 와 mapper ·
  federation 대 broker · 관리 REST API · 내보내기/가져오기 · 마무리.
  퀴즈 7. 데모는 새로 만들지 않았다 — 이 부는 실물 화면이 데모다.
- **개발:** `deck/sections/05_keycloak.html`(신규) ·
  `13_appendix.html`(FULLSRC 12개 — keycloak/ 스크립트와 설정 조각) ·
  `deck/claims.md`(5부 절 24행 + Keycloak sha256) · `deck/pending.txt`(비움)
- **검증:** 687장 · **커버리지 7588/7588줄 100퍼센트** · 조립 0건 ·
  역검증 통과 · deck-check 0건(퀴즈 37 · 데모 12) · 글꼴 통과 · test 14패키지.
- **엮은 자리:** 4부의 miniidp 와 나란히 두는 장을 여럿 뒀다 —
  안내문 칸 수(11 대 56), 토큰 클레임 표, "코드에 박은 것 대 매퍼로 고른 것".
  8장의 가짜 AD 로그가 7부의 예고편 노릇을 한다.
- **다음:** 6단계 3/3 = 7부 전반(`07_ad_federation.html`).

### [2026-09-08 16:40] 6단계(1/3) 진짜 Keycloak — 받고·띄우고·realm 을 세우고

- **판:** Keycloak **26.7.3** (2026-08-31 GA). `keycloak/VERSION` 한 줄에만 적혀 있다.
  sha256 `27a6535553c3cdcd083872ba40629efafb3475e3b758e0c6f691395561dd0f1f`.
- **개발:** `keycloak/{VERSION,fetch.sh,run_dev.sh,stop.sh,export_realm.sh,`
  `admin_api.sh,e2e_login.sh}` · `keycloak/json/*.json` 6개 ·
  `keycloak/realm-campus.json`(내보낸 것, 3,019줄) · `tools/record.sh` 9절
- **이 단계가 증명한 것:** 진짜 Keycloak 이 **3부의 가짜 AD 에 LDAP 으로 붙어**
  사용자 7명과 그룹 3개를 가져오고, **4부의 jwtool 이 그 토큰을 손 하나 안 대고
  검증한다**. 내보낸 realm 파일 하나로 빈 데이터베이스에 realm 이 다시 서고
  로그인이 통과한다(`Realm 'campus' imported`).
- **찾아 고친 것 넷:**
  1. `require_free` 가 HTTP 로만 두드려 **LDAP 유령을 못 잡았다**. 이전 실행이
     남긴 fakead 가 10389 를 물고 있어 캡처가 옛 프로세스의 출력이 됐다.
     TCP 로 붙어 보도록 바꿨다.
  2. Keycloak 은 `objectGUID` 를 **16바이트 이진값 그대로** 필터에 싣는다.
     우리 로그가 날바이트를 찍어 덱에 실을 수 없었다 — RFC 4515 §3 대로
     `\XX` 로 감싸게 했다(RED→GREEN).
  3. 그 필터가 128칸이 됐다. `)(` 이음매에서 접도록 `logFilter` 를 더했다
     (하드 컷은 `organizationalPerson` 을 두 동강 냈다 — 시험이 잡았다).
  4. AD 를 고르면 Keycloak 이 매퍼를 **알아서** 만든다. 내가 만든 것들은
     중복이었다. 그룹 매퍼 하나만 남기고, 대신 **이름이 뒤집히는 문제**를
     고쳤다 — 기본 `full name` 매퍼가 `cn`("Kim Minji")을 "이름 성" 으로
     갈라 "Kim Kim" 이 됐다. 그 매퍼를 빼고 `givenName` 매퍼를 뒀다.
- **재현성(중요):** `kc_*` 캡처 12개는 **두 번 떠도 같지 않다**. Keycloak 이
  realm 을 새로 세울 때마다 서명 열쇠를 새로 만들기 때문이다. 그 사실과
  까닭을 `out/kc_reproducible.txt` 에 캡처로 남겼다. 나머지 121개는 3회 동일.
  가장 값진 캡처(가짜 AD 로그·realm 설정·동기화 결과)는 안정적이다.
- **§2.1 이탈(기록):** `keycloak/realm-campus.json` 을 커버리지에서 뺐다(PARTIAL).
  사람이 쓴 소스가 아니라 뽑아낸 3,000줄이라 전문을 실으면 덱이 JSON 낭독이 된다.
  우리가 정한 칸은 `keycloak/json/*.json` 에 있고 그쪽은 전문이 실린다.
- **다음:** 6단계 2/3 = 5부 본문(`05_keycloak.html`, 목표 65장),
  3/3 = 7부 전반(`07_ad_federation.html`).

### [2026-09-08 17:10] 4단계 2부 본문 — 71장 + 매니페스트 (누적 587장)

- **기획:** 9개 장 — 프로세스에서 컨테이너까지 · Pod · Deployment · Service ·
  Ingress · 설정과 비밀 · Kustomize · 클러스터 없이 검사하기 · 마무리.
  퀴즈 6, 데모 2(라벨 셀렉터 매칭기 신규 · YAML 검사기 재사용).
- **개발:** `k8s/base/{namespace,lunch-app,lunch-ingress,kustomization}.yaml` ·
  `k8s/overlays/{dev,prod}/kustomization.yaml` · `k8s/examples/typo.yaml` ·
  `k8s/validate.sh` · `tools/fetch_k8s_tools.sh` · `tools/kexplain.py` ·
  `deck/sections/02_k8s.html` · `13_appendix.html`(FULLSRC 8개) ·
  `deck/demos.js`(+1) · `claims.md`(2부 절) · `Makefile`(k8s-tools · YAML 폭 검사)
- **TC:** `oidc/miniapp` 의 `pickSecret` 만 새 코드라 RED→GREEN(3건).
  매니페스트는 tier B — kubeconform `-strict` 가 관문이다.
- **검증:** 587장 · **커버리지 6853/6853줄 100퍼센트** · 조립 0건 · 역검증 통과 ·
  deck-check 0건(퀴즈 30 · 데모 12) · 글꼴 통과 · `make record` 3회 md5 동일 ·
  test 14패키지 · `sh k8s/validate.sh` 세 벌 전부 통과.
- **§8.4 이탈(기록):** PLAN 은 `kubectl explain` 과 `kubectl create --dry-run=client`
  가 오프라인으로 된다고 적었는데 **둘 다 서버를 부른다**(v1.37 에서 확인).
  그 사실 자체를 캡처로 남기고(`out/k8s_needs_server.txt`),
  필드 설명은 쿠버네티스 공개 JSON 스키마를 읽는 `tools/kexplain.py` 로 대신했다.
  오프라인으로 되는 것은 `kubectl kustomize` 와 `kubeconform` 둘뿐이다.
- **잡은 것 (둘):** ① `-strict` 없는 판의 캡처가 요점을 못 보였다 —
  typo.yaml 에는 타입 오류가 함께 있어 어느 쪽으로 돌려도 Invalid 였다.
  **오타 하나만** 있는 파일을 따로 만들어 `Valid: 1` ↔ `Invalid: 1` 로 갈리게 했다.
  ② YAML 함정 캡처를 처음에 **손으로 적은 값**으로 만들었다가
  진짜 파서에 넣어 보니 절반이 틀렸다 — 쿠버네티스의 YAML 1.2 에서
  `yes`·`NO`·`12:30` 은 글자로 남고(노르웨이 문제 없음),
  `1.20`→1.2 와 `010`→8 만 실제로 바뀐다. 캡처와 본문을 사실에 맞췄다.
- **다음:** §8 6단계(5부 Keycloak — 배포판 내려받아 실제로 띄우기, JVM 1개).

### [2026-09-08 15:40] 5단계(3/3) 4부 본문 — 116장 + 부록 확장 (누적 504장)

- **기획:** 9개 장 — 왜 위임하나 · 인가 코드 흐름 · state/nonce/PKCE ·
  토큰 세 장 · JWT 해부 · JWKS 와 안내문 · 앱 쪽 · 세 세션과 로그아웃 ·
  직접 돌려 보기. 퀴즈 8, 데모 2(PKCE 계산기 · JWT 해독기).
- **캡처:** 4부 절에서 38개. `tools/showurl.py` 를 새로 만들어
  200칸 넘는 주소를 칸마다 한 줄로 펼쳐 실었다 — 그대로는 108칸 규칙에 걸린다.
  토큰·JWKS 도 가운데를 줄인 판을 따로 떴다(`*_short.txt`).
- **개발:** `deck/sections/04_sso.html`(신규) · `13_appendix.html`(FULLSRC 11개 추가) ·
  `deck/demos.js`(+2) · `deck/claims.md`(4부 절 28행) · `deck/pending.txt`(비움) ·
  `tools/showurl.py`(신규) · `tools/record.sh` · `tools/scrub.py` ·
  `deck/sections/01_web.html`
- **검증:** 504장 · **커버리지 6465/6465줄 100퍼센트** · 조립 0건 · 역검증 통과
  (코드 274 · 출력 99) · deck-check 0건(퀴즈 24 · 데모 11) · 글꼴 통과 ·
  `make record` 3회 md5 동일 · test 14패키지.
- **장수:** 4부 116/95(목표 초과 21). 예상 합계 1089 (상한 2000).
- **근거:** 4부의 규격 주장 28건을 `claims.md` 에 URL 과 함께 적었다 —
  RFC 6749/6750/7515-7519/7636/7662/8615/8725/9068/9700, OAuth 2.1 초안,
  OIDC Core·Discovery·RP-Initiated Logout.
- **바로잡은 것:** 4부 본문을 쓰다 `alg=none` 사고의 **연도**를 적었다가
  근거를 댈 수 없어 뺐다. 대신 공격의 종류를 RFC 8725 로 댔다.
  0부의 세 세션 표와 4부 8장의 표가 C 의 정의에서 어긋나 있어 0부에 맞췄다.
- **다음:** §8 4단계(2부 쿠버네티스) 또는 6단계(5부 Keycloak).

### [2026-09-08 11:25] 5단계(1/3) OIDC 기초 — jwt · pkce · LDAP 클라이언트 분리
- **기획:** 토큰 층(`oidc/jwt`)과 PKCE(`oidc/pkce`). `miniidp` 가 AD 에 물어보려면
  LDAP 클라이언트가 **라이브러리**여야 해서 `ldapcli` 안에 있던 것을 `ldap/client` 로 뽑았다.
  그러려면 `fakead` 를 시험에서 import 할 수 있어야 해서 `ldap/fakead`(라이브러리) +
  `ldap/fakead/cmd/fakead`(main) 로 나눴다. 덱 인용 범위는 그대로다.
- **TC:** 셋 다 뼈대→RED→GREEN.
  jwt — RFC 7515 A.1 · RFC 7519 §3.1 base64url 골든, 공격 넷(alg=none · alg 혼동 ·
  내용 변조 · 남의 열쇠), 클레임 검사 7종, JWKS 왕복, kid 로 열쇠 고르기.
  pkce — RFC 7636 부록 B 벡터. client — **진짜 fakead 를 띄워 놓고** 시험한다.
- **개발:** `oidc/jwt` · `oidc/pkce` · `ldap/client`(신규) · `ldap/fakead` 분리 ·
  `ldapcli` 를 client 위로 · `tools/record.sh`
- **검증:** test 12패키지 · vet · `make record` 3회 md5 동일(54개) · 조립 0건 ·
  역검증 통과 · deck-check 0건 · 글꼴 통과 · width 18파일.
- **잡은 결함:** TLS 1.3 세션 티켓은 악수가 끝난 뒤 비동기로 온다. 몇 장이 잡히느냐가
  그때그때 달라 `-v` 캡처의 줄 번호가 밀렸고, 덱이 줄 번호로 인용하므로 흔들렸다.
  본문만 따로 뜨는 캡처(`web04_*_body.txt`)를 더해 인용을 그쪽으로 옮겼다.
- **설계 판단 하나:** `BindError.Error()` 를 짧게 줄였다가 되돌렸다. 오류를 그냥 로그로
  흘리는 쪽에서 진짜 이유(AD 의 data 코드)를 잃기 때문이다. 폭 문제는 표시 층에서 접는다.
- **다음:** 5단계(2/3) `miniidp`·`miniapp`·`jwtool`, 그다음 (3/3) 4부 본문.

### [2026-09-08 10:42] 3단계(뒤) 3부 본문 — 83장 + 전체 소스 부록 100장 (누적 309장)
- **기획:** 9개 장 — 디렉터리/DN · AD 속성 · 그룹과 memberOf · BER 바이트 ·
  바인드 · 검색과 필터 · 포트/LDAPS/서비스 계정 · 안 하는 것과 Kerberos · 마무리.
  퀴즈 8, 데모 2(LDAP 필터 해석기·DN 해석기), 그림 1(디렉터리 나무).
- **TC:** 로그 폭 시험(RED) → `Server.Close` 가 유휴 연결 때문에 안 꺼지던 **진짜 결함**을
  잡았다(연결 추적 추가). 진단 문구 접기 `wrapCells` 도 RED→GREEN.
- **개발:** `deck/sections/03_ad.html` · `13_appendix.html` · `figs/ad_tree.svg` ·
  `demos.js`(+2) · `ldap/fakead/server.go` · `ldap/ldapcli/dump.go` ·
  `order/budget/pending.txt` · `Makefile`
- **검증:** 309장 572 KB · **커버리지 3833/3833줄 100퍼센트** · 조립 0건 · 역검증 통과 ·
  deck-check 0건 · 글꼴 통과 · `make record` 2회 md5 동일 · test 8패키지 · vet.
- **§7 이탈(기록):** §7 의 표에 없던 **부록 절(13)** 을 새로 뒀다.
  `ldap/**` 2,900줄을 3부 안에 전부 실으면 가르치는 장이 통째로 코드 낭독이 된다.
  전문은 뒤에 따로 모으고(FULLSRC 가 자동 분할), 3부는 고른 조각만 가르친다.
  §2.1 의 "모든 줄이 덱에 있다" 는 약속은 그대로 지켜진다 — 조립기가 매번 센다.
- **도구가 잡은 것:** 글꼴 서브셋이 `①`(모호 폭)을 거절 → 고정폭 블록에서 `1.` 로 바꿈.
  `make width` 가 시험 파일까지 보던 것을 전문 인용 대상만 보도록 고침.
- **장수:** 1부 104/80 · 3부 83/75 · 부록 100. 예상 합계 989 (상한 2000).
- **다음:** §8 4단계(2부 k8s) 또는 5단계(OIDC 코어).

### [2026-09-08 09:20] 3단계(앞) LDAP 코어 — 소스만, 본문은 다음 커밋
- **기획:** §8 3단계. `ldap/ber`(BER 부호화) · `ldap/proto`(메시지·필터·컨트롤) ·
  `ldap/fakead`(디렉터리+서버) · `ldap/ldapcli`(바이트 풀이). 전부 표준 라이브러리.
- **TC:** 넷 다 뼈대→RED→GREEN. 골든 바이트는 익명 바인드 14바이트와
  정수·길이 표, 필터는 글↔나무↔바이트 3방향 왕복 15종.
  서버는 진짜 소켓 종단 시험 — 쪼개 보내기·쓰레기 바이트·LDAPS 악수·잠금.
- **개발:** `ldap/**` 8파일 2,300줄, `data/campus.ldif`(15항목), `tools/record.sh` 3부 절
- **검증:** test 8패키지 · vet · `make record` 2회 md5 동일(52개) · 조립 0건 ·
  역검증 통과 · deck-check 0건 · 글꼴 통과
- **AD 재현 정도(§5.4):** 진단 코드 52e·533·775·525, 잠금(창 10분·5회·30분),
  memberOf 계산(저장 아님), objectGUID 16바이트 이진값, UPN 바인드,
  페이지 컨트롤(한 쪽·빈 쿠키), 익명 검색 거절, LDAPS.
  **안 하는 것:** StartTLS · SASL/GSSAPI · modify/add/delete · referral · GC 3268.
- **다음:** 3부 본문 `03_ad.html`. `deck/pending.txt` 에 8파일이 대기 중이다.

### [2026-09-08 08:40] 2단계 1부 — 웹이 돌아가는 법 (104장, 누적 127장)
- **기획:** §7 의 1부. 9개 장(주소·요청응답·상태번호·리다이렉트·폼·쿠키·TLS·도구상자·마무리),
  퀴즈 8개, 브라우저 데모 7개, 실수 박물관 2장.
- **TC:** 02·03·04 는 뼈대 → RED → GREEN. 01 은 돌연변이로 시험이 무는지 확인.
  TLS 는 httptest 로 진짜 악수 3종. 전부 40개.
- **개발:** `web/01~04` (+테스트), `tools/record.sh`·`scrub.py`·`width.py`·`rewrap.py`,
  `deck/demos.js`, `deck/sections/01_web.html`
- **검증:** test·vet 통과 · `make record` 3회 md5 동일 · 조립 0건 · 역검증 통과 ·
  deck-check 0건 · 글꼴 통과. 커버리지: `web/**` 4파일 전부 line-exactly-once.
- **잡은 결함 둘:** (1) `scrub.py` 가 "16진수 32글자 이상" 을 전부 바꾸다가
  sha256 출력까지 가짜로 만들었다 — 덱이 거짓 해시를 실을 뻔했다. 값의 모양이 아니라
  **자리**(`lunch_session=` 등 이름을 아는 곳)로 고르도록 바꿨다.
  (2) `go run` 이 남긴 유령이 포트를 물고 있어 캡처가 **옛 코드의 출력**이었다.
  빌드 후 실행 + 포트 선점 검사로 바꿨다. 둘 다 "두 번 돌려 md5 비교" 가 잡았다.
- **도구 추가:** `tools/width.py`(폴더블 72칸을 **칸 수**로 검사 — 한글은 두 칸),
  `tools/rewrap.py`(주석 문단 자동 재배치), `deck/budget.txt`(부별 장수 예산).
- **§9 이탈 둘(기록):** ① `<pre>` 폭 상한을 코드 72칸 / **진짜 캡처 108칸** 으로 나눴다 —
  curl 의 `Set-Cookie` 한 줄이 106칸인데, 그것을 잘라 싣는 것은 "출력은 진짜다" 를 깬다.
  ② 커버리지의 "line-exactly-once" 중 **중복은 오류가 아니라 알림**으로 바꿨다.
  맥락에서 한 번·전문에서 한 번 보여 주는 편이 가르치는 데 낫다. 빠진 줄은 여전히 오류다.
- **장수:** 1부 104장 (목표 80). 예상 합계 882장 — 상한 1000 안.
- **다음:** §8 3단계(LDAP `ldap/ber`·`proto`·`fakead`·`ldapcli`) → 3부.

### [2026-09-08 07:10] 1단계 뼈대 — 조립기·0부 12장·부 표지 12장 (24장)
- **기획:** §8 1단계 그대로. 덱이 첫 커밋부터 열리도록 부 표지 12장을 먼저 세웠다.
- **TC:** `deck/check_deck.js` RED(덱 없음) → GREEN. `certs/check_certs.sh` RED(인증서 없음) → GREEN.
- **개발:** go.mod · Makefile · .gitignore · deck/{build_deck,verify_deck,chunks,gen_system}.py ·
  deck/check_deck.js · deck/base/{head,tail}.html · sections 13 · figs 13 · certs · claims.md
- **검증:** `make all SKEL=1` — 조립 0건 · 역검증 통과 · deck-check 0건 · 글꼴 --check 통과. 24장 171 KB.
- **비고(§5 이탈):** §5 는 `boricha/deck/` 도구 복사를 지시했으나, 그 계보는 `<section class="slide">`
  구조라 이 덱이 요구하는 template 의 `__demo`·`.quiz`·`#ch` 상호참조와 맞지 않는다.
  저장소의 template 계열 조립기(= `rts/deck/build_deck.py` 계보)로 바꾸고, `base/` 는
  `template.html` 을 직접 갈라 만들었다. 지시자는 `<!--CODE/OUT/FIG/FULLSRC-->` 형식이다.
  `hl.py`·`gen_fonts.py` 는 불필요 — 강조는 템플릿 런타임 하이라이터가, 글꼴은
  `tools/embed_mono_font.py` 가 맡는다. `player.js`·`gen_appendix.py` 도 §5 대로 쓰지 않는다.
- **다음:** §8 2단계(1부 웹 사다리 `web/01~04`) 와 3단계(LDAP) 는 서로 겹치지 않아 병렬 가능.
