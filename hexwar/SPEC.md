# HexWar Engine Specification (normative)

All three implementations (Python / Lua / TypeScript) MUST follow this document
exactly. Any deviation shows up as a golden-vector mismatch.

Everything here is INTEGER arithmetic unless a section explicitly says otherwise.
The one place floating point is allowed is the *reference* pixel->hex routine in
§4.2, which exists only to validate the integer routine of §4.3.

---

## 1. Coordinates

### 1.1 Axial and cube

Axial coordinate is a pair `(q, r)`. Cube coordinate is a triple `(x, y, z)` with

    x = q          z = r          y = -x - z          (so x + y + z == 0)

### 1.2 Orientation

The engine is built for **pointy-top** hexes laid out in **rows** (`odd-r` offset).
Flat-top / `odd-q` conversions are also implemented (they appear in the deck) but the
map, renderer and picker use pointy-top odd-r.

### 1.3 Offset conversion (odd-r, pointy-top)

`col`,`row` are the storage indices; `row` is the hex row, offset to the RIGHT on odd rows.

    axial_to_oddr(q, r):  col = q + ((r - (r & 1)) >> 1)   ; row = r
    oddr_to_axial(col,row): q = col - ((row - (row & 1)) >> 1) ; r = row

`>>` is an ARITHMETIC shift; `r & 1` on a negative `r` must yield 0 or 1 (i.e. the
mathematical parity, never -1). Implementations that lack arithmetic shift on
negatives must use `floordiv(r - (r & 1), 2)`.

### 1.4 Offset conversion (odd-q, flat-top) — deck only

    axial_to_oddq(q, r):  col = q ; row = r + ((q - (q & 1)) >> 1)
    oddq_to_axial(col,row): q = col ; r = row - ((col - (col & 1)) >> 1)

### 1.5 Direction table (canonical order, pointy-top axial)

    index  name  dq  dr
      0    E     +1   0
      1    NE    +1  -1
      2    NW     0  -1
      3    W     -1   0
      4    SW    -1  +1
      5    SE     0  +1

`neighbor(h, d) = (h.q + dq[d], h.r + dr[d])`.
Direction indices are part of the wire format: save files and golden traces store them.

### 1.6 Distance

    dist(a, b) = (|ax-bx| + |ay-by| + |az-bz|) / 2       (cube form; always exact)

Equivalent axial form used by the code (avoids computing y):

    dq = a.q - b.q ; dr = a.r - b.r
    dist = ( |dq| + |dr| + |dq + dr| ) / 2

### 1.7 Rotation and reflection

Directions are named for the screen (`r` grows downward), so `E -> SE` is clockwise
and the direction table of §1.5 (E, NE, NW, ...) runs counter-clockwise.
Rotate one step clockwise about the origin:  `(x,y,z) -> (-z,-x,-y)`.
Counter-clockwise: `(x,y,z) -> (-y,-z,-x)`. Rotation about a center `c`: translate to origin,
rotate, translate back. Reflection across the q axis: `(x,y,z) -> (x,z,y)`.

### 1.8 Ring and spiral

`ring(center, N)` for `N >= 1`: start at `center + dir[4]*N` (SW corner) and walk
`dir[d]` for `d = 0..5`, `N` steps each — 6N hexes, first element is the start.
`ring(center, 0)` is `[center]`.
`spiral(center, N)` = `ring(center,0) ++ ring(center,1) ++ ... ++ ring(center,N)`,
count `1 + 3N(N+1)`.

### 1.9 Line

`lerp` on cube coords with a fixed-point nudge; see §9.1 (LOS uses the same line).

---

## 2. Map storage

### 2.1 Geometry

    MAP_W = 24 columns, MAP_H = 18 rows        (odd-r offset storage)

Storage index `i = row * MAP_W + col`, row-major, no padding in the reference layout.
A *sentinel-padded* variant is described in the deck but not used by the engine.

### 2.2 Cell byte

Every cell is packed into ONE unsigned byte, laid out MSB..LSB:

    bit 7   : road       (1 = a road runs through this hex)
    bit 6-4 : elevation  (0..7)
    bit 3-0 : terrain id (0..15)

    pack(terrain, elev, road) = (road << 7) | (elev << 4) | terrain
    terrain(c) = c & 0x0F ; elev(c) = (c >> 4) & 0x07 ; road(c) = (c >> 7) & 1

### 2.3 Terrain table

    id  key       name(ko)  move  def  losBlock  losHeight
     0  CLEAR     평지        2     0      0         0
     1  FOREST    숲          4     2      1         1
     2  HILL      언덕        4     1      0         1
     3  MOUNTAIN  산          6     3      1         2
     4  CITY      도시        2     4      1         1
     5  RIVER     강          6     1      0         0
     6  SWAMP     늪          6     0      0         0
     7  SEA       바다       -1     0      0         0      (-1 = impassable)

`move` is in movement points (MP). Clear costs 2 so that a road can cost 1.
Moving into a hex that has `road == 1` FROM a hex that also has `road == 1`
costs 1 MP regardless of terrain (river fords count as road when road bit set).
`losHeight` is added to `elev` when testing whether a hex blocks sight (§9.2).

### 2.4 Parallel arrays (structure of arrays)

    cells   : uint8  [MAP_W * MAP_H]     packed per §2.2
    fog     : uint8  [MAP_W * MAP_H]     0 = hidden, 1 = explored, 2 = visible
    occupant: int16  [MAP_W * MAP_H]     unit id, or -1

The deck contrasts this with an array-of-structs layout and measures both.

---

## 3. Units

### 3.1 Record

    id        int      index into the unit pool, stable for the whole game
    side      int      0 = 청군(player), 1 = 적군
    kind      int      index into the unit-kind table
    q, r      int      axial position
    hp        int      0..10
    mp        int      movement points left this turn
    ammo      int      0..8
    ent       int      entrenchment 0..3
    alive     bool

### 3.2 Unit kind table

    id  key       name(ko)   mp  atk  def  rng  vis  hpmax  ammo
     0  INF       보병        6    4    5    1    2    10     6
     1  TANK      전차       12    8    6    1    2    10     6
     2  ARTY      포병        6   10    2    3    2     8     5
     3  RECON     정찰       16    3    3    1    4    10     4

`rng` is attack range in hexes, `vis` is vision radius in hexes.

### 3.3 Pool and free list

Units live in a fixed array of `MAX_UNITS = 64`. Dead units are pushed onto a
free-list (`freeHead`, `next[]`) so ids can be recycled; the golden trace exercises
recycling. `occupant[]` is the reverse index and MUST always agree with the unit
positions — `assertOccupantConsistent()` is called after every command in debug runs.

---

## 4. Pixel <-> hex

### 4.1 Screen layout

Mode 13h framebuffer: 320 x 200, 8-bit indexed.

    HEX_W    = 32     hex bounding box width  (pointy-top: full width)
    HEX_H    = 32     hex bounding box height
    ROW_STEP = 24     vertical distance between hex rows (3/4 of HEX_H)
    ODD_SHIFT= 16     odd rows shifted right by HEX_W/2

Hex `(col,row)` in odd-r storage has its bounding-box top-left corner at

    px = col * HEX_W + (row & 1) * ODD_SHIFT - camX
    py = row * ROW_STEP - camY

The map viewport is the rectangle `(0,0)-(256,168)` of the screen; the right 64
columns are the side panel and the bottom 32 rows are the message bar.

### 4.2 Hex outline (stretched hexagon, integer slopes)

A 32x32 bounding box is NOT a regular hexagon (a regular pointy-top hex 32 wide is
36.95 tall). DOS games stretched it on purpose so the slanted edges land on integer
slopes. Vertices of the hex whose bounding box top-left is `(L, T)`:

    (L+16, T)      (L+32, T+8)    (L+32, T+24)
    (L+16, T+32)   (L,    T+24)   (L,    T+8)

Both slanted edges rise 8 pixels over 16 — slope exactly 1/2, so every edge pixel is
computed with a shift, never a multiply-divide.

Point-in-hex, in local coordinates `px = x - L`, `py = y - T`, half-open on every
boundary so the plane is partitioned exactly:

    py <  8         : inside iff  16 - 2*py <= px < 16 + 2*py
    8 <= py < 24    : inside iff  0 <= px < 32
    24 <= py < 32   : inside iff  2*(py-24) <= px < 32 - 2*(py-24)

`tools/picker_check.py` uses this test over the whole map as the independent
reference and compares it against §4.3 for all 320x200 screen pixels at several
camera positions.

### 4.3 The DOS picker: brick + mask table — NORMATIVE

Screen point `(mx, my)` with camera `(camX, camY)`:

    yy = my + camY
    by = floor_div(yy, ROW_STEP)          ; oy = yy - by*ROW_STEP        (0..23)
    xx = mx + camX - (by & 1) * ODD_SHIFT
    bx = floor_div(xx, HEX_W)             ; ox = xx - bx*HEX_W           (0..31)
    v  = PICK_MASK[oy*32 + ox]

`floor_div` is floor division (rounds towards -inf), so negative camera offsets work.
`by & 1` must be the mathematical parity for negative `by` too.

    v = 0 -> the brick's own hex        (col, row) = (bx, by)
    v = 1 -> the NW neighbour of (bx, by)
    v = 2 -> the NE neighbour of (bx, by)

with the odd-r neighbour rules

    row even: NW = (col-1, row-1)   NE = (col,   row-1)
    row odd : NW = (col,   row-1)   NE = (col+1, row-1)

The table itself is generated by `tools/gen_prim.py` from §4.2 and is equivalent to

    v = 1 if (oy < 8 and ox <  16 - 2*oy)
    v = 2 if (oy < 8 and ox >= 16 + 2*oy)
    v = 0 otherwise

DOS code shipped the 768-byte table rather than the formula because a segment-offset
byte fetch cost far less than two multiplies and three branches on an 8086. Only the
top 8 rows of a brick are ambiguous; rows 8..23 always resolve to the own hex, which
is why the table is mostly zeros and compresses to nothing.

`golden/pick_mask.txt` holds it as 24 lines of 32 digits, and all three
implementations embed that same table.

### 4.4 Cube rounding (fixed point)

Inputs are fixed-point cube coordinates `(xf, yf, zf)` in units of `1/SCALE`.

    round_div(n, d)   for d > 0, ties away from zero:
        n >= 0 ->   (2*n + d) // (2*d)
        n <  0 -> -((-2*n + d) // (2*d))

    rx = round_div(xf, SCALE) ; ry = round_div(yf, SCALE) ; rz = round_div(zf, SCALE)
    dx = |rx*SCALE - xf| ; dy = |ry*SCALE - yf| ; dz = |rz*SCALE - zf|
    if dx > dy and dx > dz : rx = -ry - rz
    elif dy > dz           : ry = -rx - rz
    else                   : rz = -rx - ry

The comparison order (`dx` first, then `dy`) is part of the specification: it decides
which hex a point exactly on an edge belongs to, and the three ports must agree.

---

## 5. Random numbers

32-bit LCG (Numerical Recipes constants), identical in all three languages:

    state = (state * 1664525 + 1013904223) mod 2^32
    next():  state = ...; return state
    d6():    return ((state >> 16) mod 6) + 1     -- state AFTER advancing

TypeScript MUST use `Math.imul(state, 1664525)` and `>>> 0` to stay in 32 bits.
Python and Lua mask with `& 0xFFFFFFFF`.
The game seeds the LCG with `0x1BADB002` at scenario start.

---

## 6. Movement and pathfinding

### 6.1 Cost

    cost(from, to, side):
      t = terrain(to)
      if move[t] < 0                      -> impassable
      if occupant[to] is an enemy unit    -> impassable
      if occupant[to] is a friendly unit  -> impassable (no stacking)
      if road(from) and road(to)          -> 1
      else                                -> move[t]

### 6.2 Zone of control

A hex is in enemy ZOC if any of its 6 neighbours holds a living enemy unit.
Entering a ZOC hex is legal but sets remaining MP to 0 (movement stops).
The start hex being in ZOC does not restrict leaving it.

### 6.3 Reachable set — Dial's bucket queue

Costs are small integers (1..6) and the MP budget is <= 16, so the frontier is kept
in `maxMP+1` buckets indexed by remaining cost. `reachable(unit)` returns a map from
storage index to `(costSpent, cameFromDirection)`. Complexity O(V + E + maxMP).
Ties are broken by the bucket scan order, which is why the algorithm is
deterministic and safe to put in a golden vector.

### 6.4 A*

For a target beyond the MP budget the engine plans a multi-turn route with A* using

    h(a, b) = dist(a, b) * MIN_COST        MIN_COST = 1

which is admissible (every step costs >= 1) and consistent. The open set is a binary
heap keyed by `(f, insertionOrder)`; the insertion counter makes tie-breaking
deterministic across languages. This is the only place a heap is used; §6.3 explains
why the bucket queue is better on the small maps DOS games actually shipped.

---

## 7. Combat

    attack(att, def):
      a = atk[att.kind] * att.hp / 10                       integer division
      d = def[def.kind] * def.hp / 10 + terrainDef + def.ent
      roll = d6() + d6()                                     2..12
      score = a - d + roll - 7
      if score >= 4 : defender loses 3 hp, attacker loses 0
      elif score >= 1: defender loses 2 hp, attacker loses 1
      elif score >= -2: defender loses 1 hp, attacker loses 1
      else          : defender loses 0 hp, attacker loses 2
      attacker spends 1 ammo and all remaining MP
      a defender at range 1 with ammo > 0 and rng >= 1 returns fire for half damage
      (integer division by 2, rounded down), spending 1 ammo

Deaths are resolved after both sides have applied damage.

---

## 8. Turn structure

    scenario start -> side 0 turn -> side 1 turn (AI) -> side 0 turn -> ...

At the start of a side's turn: every living unit of that side gets `mp = mp[kind]`,
regains 1 entrenchment level (max 3) if it did not move last turn, and visibility is
recomputed for that side.

Victory: a side wins when the enemy has no living units, or when side 0 occupies
both objective hexes at the end of its turn. Scenario also ends at turn 20 (draw).

---

## 9. Line of sight and fog

### 9.1 Hex line (supercover-free, one hex per step)

    N = dist(a, b)
    for i in 0..N:
       t = i / N                     (computed as a rational, see below)
       cube_lerp with the epsilon nudge  a + (b - a) * t  applied to (x,y,z)
       cube_round (§4.4)

To keep all three languages identical the interpolation is done in FIXED POINT:

    SCALE = 1024
    ti    = i * SCALE / N                         integer division
    xf    = ax*SCALE + (bx-ax)*ti + NUDGE_X        NUDGE_X = +1  (in 1/SCALE units)
    yf    = ay*SCALE + (by-ay)*ti + NUDGE_Y        NUDGE_Y = +1
    zf    = az*SCALE + (bz-az)*ti + NUDGE_Z        NUDGE_Z = -2
    then cube_round on (xf/SCALE, yf/SCALE, zf/SCALE) computed with rounded
    integer division that ties away from zero.

The nudge sums to zero so the point stays on the x+y+z=0 plane; it breaks the
exact-half ties that otherwise make a line ambiguous on hex edges.

### 9.2 Blocking

Observer at `a` with eye height `H(a) = elev(a) + losHeight(terrain(a)) + 1`.
Target at `b` with height `H(b) = elev(b) + losHeight(terrain(b))`.
For each intermediate hex `m_i` (i = 1..N-1) with height `H(m_i)`, sight is blocked if

    H(m_i) * N  >  H(a) * (N - i) + H(b) * i

i.e. the hex pokes above the straight line drawn from the observer's eye to the
target. Multiplying by `N` keeps it in integers.

### 9.3 Fog

Per side, `fog[i]` is `0` hidden / `1` explored / `2` visible. Recomputing visibility
for a side: set every `2` down to `1`, then for each living unit of that side mark
its spiral(vis) hexes that pass the LOS test back up to `2`.

---

## 10. Rendering

### 10.1 Framebuffer and palette

`fb` is a `320*200` byte array, index 0 = transparent when blitting sprites but a
real colour (black) in the framebuffer. The palette is 256 entries of `(r,g,b)`
with each component `0..63` (VGA DAC range). `golden/palette.txt` holds it as 256
lines of `r g b`. PPM output scales each component with `v * 255 // 63`.

### 10.2 Sprites

    sprite = { w, h, data[w*h] }    index 0 = transparent

RLE format (`golden/tiles.rle`, one sprite per block, `;` starts a comment line):

    line 1 : name w h
    line 2+: whitespace separated "count value" pairs, count 1..255, row-major,
             read until the counts sum to w*h; then the next block begins

`blit(fb, sp, x, y, clip)` skips index 0, clips to the given rectangle.

### 10.3 Dirty rectangles

The renderer keeps `dirty` as a list of rectangles in screen space, merged when they
overlap by more than 50% of their union area. A frame redraws only dirty rectangles;
`--full` forces a whole-screen redraw. The golden frame is produced with `--full`
so it does not depend on the dirty-rect history.

### 10.4 Frame hash

    FNV-1a 32-bit over the raw PPM bytes:
      h = 2166136261
      for each byte b: h = ((h XOR b) * 16777619) mod 2^32

TypeScript uses `Math.imul` for the multiply.

---

## 11. UI

### 11.1 Widget tree

Widgets are records `{id, x, y, w, h, kind, label, enabled, visible, children}`.
Hit testing walks the tree back-to-front and returns the topmost widget whose
rectangle contains the point and which is `visible && enabled`.

Kinds: `PANEL`, `BUTTON`, `LABEL`, `MINIMAP`, `MAPVIEW`, `LOG`, `DIALOG`.

### 11.2 State machine

    IDLE            -- no selection
    SELECTED        -- a friendly unit is selected, reachable set computed
    TARGETING       -- choosing an attack target
    DIALOG          -- modal dialog open, map input suppressed
    GAMEOVER

Transitions are listed in `golden/fsm.txt` and the trace exercises every edge.

### 11.3 Commands and undo

Every state change goes through a command record:

    {kind: MOVE|ATTACK|ENDTURN, unit, from, to, path, undoState}

`undoState` captures the minimal fields needed to reverse the command (unit mp, hp,
ammo, ent, position; defender hp/ammo; the RNG state BEFORE the command; fog snapshot
is NOT captured — fog is recomputed). The undo stack is cleared at end of turn.

---

## 12. Golden vectors

    golden/prim.json    hand-derived primitive expectations (§1, §4, §5, §9)
    golden/pick_mask.txt 24 lines x 32 digits (§4.3)
    golden/palette.txt  256 lines "r g b"
    golden/tiles.rle    sprite corpus
    golden/trace.jsonl  one JSON object per scripted step (frozen from the reference)
    golden/scenario.txt the map and starting units, as text

`trace.jsonl` step object:

    {"step":N,"ev":"click 120 88","state":"SELECTED","sel":7,"turn":1,"side":0,
     "rng":123456789,"unitHash":"...","fogHash":"...","fbHash":"..."}

`unitHash`/`fogHash` are FNV-1a over a canonical text serialisation defined in
`§12.1`; `fbHash` is §10.4 and is only present on steps marked `render`.

### 12.1 Canonical serialisation

    units: for each id 0..MAX_UNITS-1 that is alive, in id order:
           "id,side,kind,q,r,hp,mp,ammo,ent\n"
    fog:   MAP_H lines of MAP_W digits, top row first
