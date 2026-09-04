# HexWar — DOS-era hex tile game anatomy (deck + 3-language engine)

Agent-facing plan. Language: English here; all user-facing output and deck body text is Korean.

## Goal

One self-contained slide deck at repo root:

    도스_헥사곤_타일게임_해부.html      ~380-420 slides (up to 500 allowed)

plus a committed, runnable 3-language implementation of the same hex tactical
wargame engine under `hexwar/`:

    hexwar/py/    Python 3   (reference implementation)
    hexwar/lua/   Lua 5.4+   (port)
    hexwar/ts/    TypeScript (port, compiled with tsc, run on node)

The deck carries the FULL SOURCE of all three (budget ~4,500 lines total), every
listing pulled from disk by `data-src` and re-verified byte-for-byte.

## Non-negotiables

1. Every code block in the deck comes from a real file in `hexwar/` and is verified
   by `deck/verify_deck.py` (byte comparison). No hand-typed code in the deck body.
2. Every terminal/output block comes from a real run captured under `hexwar/out/`.
3. The three implementations are proven equivalent by golden vectors:
   identical primitive results, identical scripted-scenario trace, and a
   byte-identical rendered PPM frame (compared by FNV-1a hash).
4. Historical claims about real DOS games (titles, years, engines, resolutions)
   are verified with WebSearch before they go in. Never invent a number.
5. Deck must open offline as a single file: no CDN, no web fonts, no external images.

## Order of work

1. `SPEC.md`   — normative engine spec (this fixes all three ports).            [done first]
2. `golden/prim.json` — hand-derived primitive vectors. RED: no implementation yet.
3. `py/`       — reference implementation, module by module, tests green.
4. `golden/trace.json` — frozen from the reference once primitives pass.
5. `lua/`, `ts/` — ports; parity against the frozen golden vectors.
6. `out/`      — captured runs (traces, PPM renders, timings).
7. `deck/sections/*.html` — slide fragments, part by part.
8. `deck/build_deck.py` — assemble; `deck/verify_deck.py` — reverse-verify.
9. `index.html` card + `README.md` entry + `history.md` — one commit.

## Deck structure (target ~400 slides)

  1부  도스라는 무대            하드웨어·화면 모드·640KB·정수 산술          20
  2부  왜 육각형인가            격자 비교·실제 도스 게임 고증               16
  3부  좌표계의 수학            offset/axial/cube·거리 증명·이웃·링·회전    34
  4부  픽셀과 헥스 사이         기하·마스크 룩업 피킹·정수 근사·반올림      28
  5부  맵 자료구조              배열 배치·비트 패킹·SoA/AoS·캐시            30
  6부  타일 렌더링              오프스크린·마스크/RLE 스프라이트·더티·스크롤 34
  7부  GUI 셸                   이벤트 루프·위젯·히트테스트·FSM·언두        36
  8부  경로 탐색                다익스트라·버킷 큐·A*·ZOC·이동범위          32
  9부  시야와 안개              슈퍼커버 라인·고도 LOS·안개 비트            24
 10부  유닛·턴·전투             레코드·프리리스트·LCG·CRT·세이브            26
 11부  파이썬 전문              reference 구현 전체                         38
 12부  루아 전문                포트 + 언어 차이                            32
 13부  타입스크립트 전문        포트 + 타입드 어레이                        34
 14부  파리티 증명과 마무리     골든 벡터·성능 비교·현대 대응표·체크리스트  20
