# SCENARIO — "보물상사 가을 워크숍 준비" (contract for all three languages)

This file is the single source of truth for the scenario. Python, TypeScript and Go implement
exactly this; `ex/fixtures/golden/*.json` pins the results and every language's tests read
them. If a rule here changes, change the fixture/golden first, then all three code bases.
Korean strings below are exact (agents print/return them byte-for-byte).

## 1. Story

보물상사(가상의 회사) 총무팀이 기획 에이전트에게 말한다:

> `2026-10-30부터 1박 2일, 30명(채식 2명), 예산 6,000,000원, 출발 강남역`

기획 에이전트(planner)는 Agent Card로 동료 에이전트를 찾고, 숙소·식사·교통을 **동시에**
맡긴 뒤, 세 견적을 정산 에이전트에 넘겨 승인을 받고, 워크숍 계획서를 돌려준다.

## 2. Domain data (`ex/fixtures/workshop.json`)

All money is integer KRW. JSON field names are camelCase (like A2A's own JSON).

### 2.1 Lodging venues

| id | name | capacity | roomSize | pricePerPersonNight | closed (dates) |
|---|---|---|---|---|---|
| `gapyeong-solsup` | 가평 솔숲 리조트 | 40 | 4 | 70000 | 2026-10-23, 2026-12-31 |
| `yangpyeong-river` | 양평 강변 연수원 | 28 | 2 | 55000 | 2026-12-31 |
| `chuncheon-lake` | 춘천 호수 펜션촌 | 60 | 6 | 62000 | 2026-10-30, 2026-12-31 |

Rule `chooseLodging(date, nights, headcount)`: candidates have `capacity >= headcount` and
none of the nights `date … date+nights-1` is closed. Pick minimum
`total = headcount * pricePerPersonNight * nights`; tie → smaller `id`. `rooms =
ceil(headcount / roomSize)`. No candidate → rejected with reason `가능한 숙소가 없습니다`.

### 2.2 Meals

Meal slots for `nights = n`: for i in 1..n: `day{i}-dinner`, `day{i+1}-breakfast`; then
`day{n+1}-lunch` (2n+1 slots, in that order). Slot type = suffix (dinner/breakfast/lunch).

| type | option id | name | price | vegetarian |
|---|---|---|---|---|
| dinner | `bbq` | 숯불 바비큐 | 32000 | no |
| dinner | `hanjeongsik` | 한정식 | 28000 | no |
| dinner | `mushroom-hotpot` | 버섯 전골 | 24000 | yes |
| breakfast | `baekban` | 한식 백반 | 9000 | no |
| breakfast | `toast` | 토스트 세트 | 7000 | yes |
| lunch | `makguksu` | 막국수와 수육 | 15000 | no |
| lunch | `bibimbap` | 산채 비빔밥 | 12000 | yes |

Caps per person per meal type (defaults, overridable in the request):
dinner 30000, breakfast 10000, lunch 15000.
Rule `planMeals(nights, headcount, vegetarians, caps)`: per slot, regular eaters
(`headcount - vegetarians`) get the most expensive non-vegetarian option with
`price <= cap` (tie → smaller id); vegetarians get the most expensive vegetarian option
with `price <= cap`. No fitting option → rejected `예산 안에 맞는 메뉴가 없습니다`.
`total = Σ slots (regular*price + veg*vegPrice)`.

### 2.3 Buses

| id | seats | pricePerDay | plate |
|---|---|---|---|
| `bus25` | 25 | 450000 | 서울 70바 2525 |
| `bus45` | 45 | 600000 | 서울 70바 4545 |

Rule `chooseBuses(headcount, nights)`: `days = nights + 1`; choose counts (a of bus45,
b of bus25) with `45a + 25b >= headcount` minimising cost per day; tie → fewer vehicles,
then more bus45. `total = costPerDay * days`.
Dispatch steps (long-running, one status update each, `stepMs` default 300, overridable
by `--step-ms`): `배차 요청 접수` → `기사 배정` → `차량 확정`.

### 2.4 Settlement

`settle(items, budget, approvalThreshold=3000000)`: `total = Σ items.amount`.
`total > budget` → rejected `예산을 초과합니다` (with the overshoot).
`total > approvalThreshold` → needs approval (AUTH_REQUIRED) unless the request carries
an approval token with scope `payment:approve`. Completed → artifact `정산서`
{items, total, budget, remaining, approvedBy}.

### 2.5 Parsing the free-text request (planner)

Regexes (RE2-compatible — Go has no lookbehind; first match wins):
vegetarians `채식\s*(\d+)명` (default 0) — **then that match is removed from the text**
before the headcount search, so `채식 2명 포함 30명` gives 30, not 2;
date `(\d{4}-\d{2}-\d{2})`, nights `(\d+)박`, headcount `(\d+)명`,
budget `예산\s*([\d,]+)원` (commas removed; absent → null), depart `출발\s*(\S+)` (absent →
null). Missing date/nights/headcount → `{"ok":false,"missing":[…]}` in the order
date, nights, headcount → planner asks (INPUT_REQUIRED).

### 2.7 Validation and result shapes

The exact JSON shapes of every result (ok and not ok) are pinned by
`ex/fixtures/golden/domain.json` — implement to that file. Validation reasons:
`인원과 박 수는 1 이상이어야 합니다` (headcount < 1 or nights < 1, checked first in
lodging/meals/buses), `채식 인원은 0명 이상, 전체 인원 이하여야 합니다`.
In `planMeals`, a side with zero people is `null` (no option needed). `caps` in the input
is merged over `defaultCaps` key by key. Bus `vehicles` lists bus45 before bus25 and omits
zero counts. `settle` checks over-budget before approval.

### 2.6 Canonical result for the story (pinned in golden)

- lodging: `gapyeong-solsup`, 8 rooms, 2,100,000 (춘천 is closed 10-30, 양평 too small)
- meals: 28 regular × (28,000 + 9,000 + 15,000) + 2 veg × (24,000 + 7,000 + 12,000)
  = 1,456,000 + 86,000 = **1,542,000**
- bus: 1 × bus45, 2 days = **1,200,000**
- settlement: total **4,842,000**, budget 6,000,000, remaining **1,158,000**, needs approval
  (> 3,000,000).

Other golden cases (at least): 2026-11-06/30명 → 춘천 1,860,000 5 rooms; 20명 → 양평
1,100,000 10 rooms; 2026-12-31 → rejected; 70명 → lodging rejected, bus 45+25 per day;
caps that exclude every vegetarian option → meals rejected; over-budget settlement.

## 3. Agents (A2A surface)

Every agent: CLI `--port P` (bind 127.0.0.1:P) and optional `--url U` (the public URL
advertised in the card; default `http://127.0.0.1:P/`). JSON-RPC binding at `/` unless the
part says otherwise. Cards are served at `/.well-known/agent-card.json`.

| agent | card name | skill id / tags | input | output | A2A features |
|---|---|---|---|---|---|
| lodging | 보물상사 숙소 에이전트 | `find-lodging` / lodging, workshop | DataPart `{date,nights,headcount}`; follow-up text `30명` or DataPart `{headcount}` | Task COMPLETED + artifact `숙소 견적` (DataPart) | blocking send → Task; INPUT_REQUIRED (`인원은 몇 명입니까?`) multi-turn on same taskId/contextId; REJECTED |
| catering | 보물상사 식사 에이전트 | `plan-meals` / meals, workshop | DataPart `{nights,headcount,vegetarians,caps?}` | streamed: WORKING status per slot (`식단 짜는 중 1/3`…), artifact `식단표` chunks (`append`, `lastChunk`), then FilePart `menu.md` (text/markdown, raw) + DataPart quote | SendStreamingMessage, artifact chunking |
| bus | 보물상사 교통 에이전트 | `book-bus` / transport, workshop | DataPart `{headcount,nights,depart}` | Task returned immediately (SUBMITTED), then WORKING ×3 steps, COMPLETED + artifact `배차 확인서` | returnImmediately, push notifications (webhook with token), GetTask polling, ListTasks, CancelTask (→ CANCELED), SubscribeToTask |
| settlement | 보물상사 정산 에이전트 | public: `check-budget`; extended card adds `settle-budget` | DataPart `{items:[{name,amount}],budget}` | AUTH_REQUIRED → after approval COMPLETED + artifact `정산서` | securitySchemes (OAuth2 client-credentials, token URL on the same server `/oauth/token`), Bearer check, extended Agent Card, signed card (JWS EdDSA/Ed25519 over JCS — deterministic signatures, so captures are stable and the three SDKs can be compared byte for byte; key in `ex/fixtures/keys/`), in-task authorization |
| planner | 보물상사 기획 에이전트 | `plan-workshop` / workshop, orchestration | text (§2.5) | streams progress; artifact `워크숍 계획서` (text/markdown) + DataPart summary | client of the four: discovery by card + skill tags, parallel fan-out with one contextId, referenceTaskIds to settlement |

Local OAuth2 issuer: `POST /oauth/token` (form `grant_type=client_credentials`,
`client_id`, `client_secret`, `scope`). Clients in `ex/fixtures/clients.json`
(`planner` / `planner-secret`, scopes `payment:read payment:approve`; `intern` /
`intern-secret`, scope `payment:read`). Tokens are deterministic opaque strings
`tok-<client_id>-<n>` (teaching only — the deck says why real tokens must be random).

Budget extension URI: `https://treasure-house.example/a2a/ext/budget/v1` (part 14).

## 4. Code layout (same shape in every language)

| | Python | TypeScript | Go |
|---|---|---|---|
| domain rules (pure) | `ex/py/workshop/domain.py` | `ex/ts/workshop/domain.ts` | `ex/go/workshop/domain.go` |
| fixture loading | `ex/py/workshop/fixtures.py` | `ex/ts/workshop/fixtures.ts` | `ex/go/workshop/fixtures.go` |
| golden tests | `ex/py/workshop/test_domain.py` (unittest) | `ex/ts/workshop/domain.test.ts` (`node --test`) | `ex/go/workshop/domain_test.go` |
| final agents | `ex/py/agents/<name>.py` | `ex/ts/agents/<name>.ts` | `ex/go/agents/<name>/main.go` |

Parts 2–14 build smaller, focused versions under `ex/<lang>/NN/`; part 15 shows the final
agents (via `region=` excerpts) and runs the whole story across languages.
