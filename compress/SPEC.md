# SPEC — bit-exact specification of the Tier-1 modules

> Audience: the five implementations (Python, Go, C++, Java, TypeScript).
> Written in English per the global language policy; the deck body that explains
> these formats is Korean.
>
> **Why this file exists.** Five implementations of "Huffman coding" will agree on
> nothing. They will disagree on tie-breaking, on header layout, on bit order, on
> what happens with an empty file. Every such disagreement is invisible until the
> golden vectors (`golden/<algo>/<file>.sha256`) diverge, and by then it is a
> five-way debugging session. So every choice is pinned here **before** the Python
> reference is written, and the reference is written from this file.
>
> **Rule:** if an implementation disagrees with this file, the implementation is
> wrong. If this file is genuinely ambiguous, fix this file first (its own commit,
> stating what was ambiguous), then the implementations, then regenerate goldens.
> Never resolve a disagreement by editing a golden vector.

---

## 0. Conventions that hold everywhere

### 0.1 Types and arithmetic

| Name | Meaning |
|---|---|
| `u8` `u16` `u32` `u64` | unsigned integers of that width, wrapping on overflow |
| `i64` | two's-complement signed 64-bit |
| `u16le` `u32le` `u64le` | little-endian byte order in the stream |
| `varint(v)` | LEB128, §2.1 |

- **No floating point.** Not in an encoder, not in a decoder, not in a model, not
  in a table. Entropy, PSNR and SNR are computed only in `bench/` (Python) and
  reach the deck as captured text. This is what makes five-language parity possible.
- **Shifts.** `x >> k` on an unsigned value is a logical shift. Java has no
  unsigned types: every unsigned right shift is `>>>`, and every byte read from an
  array is `b & 0xFF`. TypeScript's `|0`/`>>>0` traps are the mirror image — see
  §0.5.
- **Division** is never needed on a codec path except by powers of two.

### 0.2 Interface

Every module exposes exactly two functions on byte arrays:

```
encode(src: bytes) -> bytes
decode(src: bytes) -> bytes
```

`decode(encode(x)) == x` for every `x`, including the empty input. A decoder that
is handed malformed input raises/returns an error in its language's idiom
(Python `ValueError`, Go `error`, C++ `std::runtime_error`, Java
`IllegalArgumentException`, TS `throw new Error`). It must never loop forever, read
out of bounds, or allocate based on an unvalidated length field.

### 0.3 Empty input

`encode(b"")` is **not** the empty output: it is the header for length 0 and
nothing else. Every Tier-1 codec except `deflate` starts with `varint(n)` where `n`
is the original byte count, so `encode(b"")` is the single byte `0x00` — with two
exceptions, both of which fall out of the format rather than being special cases:

- **`bitio`** is `00 00`. Its body begins with three pad bits (§1.4), and three
  bits still have to be flushed into a byte. Suppressing them when `n == 0` would
  put a conditional into the format itself, which is worse than a two-byte file.
- **`deflate`** is `03 00` (§10.6). It is a real format and has its own empty form.

This is the kind of thing a spec gets wrong the first time: the sentence
"`encode(b"")` is one byte" was written before §1.4 existed, and the `bitio` test
for the empty input is what caught the contradiction.

### 0.4 Bit order

Two bit orders appear in this deck and they are not interchangeable:

- **MSB-first** — the first bit written lands in bit 7 of the first byte.
  Used by: everything in this deck except DEFLATE. It is what you get when you
  read a bit stream the way you read a number.
- **LSB-first** — the first bit written lands in bit 0 of the first byte.
  Used by: DEFLATE (RFC 1951 §3.1.1), and therefore by gzip and zlib.

Every module below names which one it uses. `bitio` implements both.

### 0.5 The three traps that actually break parity

Named here because each one cost a real debugging session in an earlier deck, and
because they are invisible until the SHA-256 differs.

1. **Java has no unsigned.** `byte` is signed. Every `src[i]` used as a value is
   `src[i] & 0xFF`. Every right shift on a value that is conceptually unsigned is
   `>>>`. `int` is 32-bit and wraps silently — the range coder (§8) relies on that
   wrap and it is correct there, but nowhere else.
2. **TypeScript numbers are doubles.** Bitwise operators coerce to **signed** 32
   bits, so `0x80000000 | 0` is negative and `range >> 8` on a value with the top
   bit set is wrong. Use `>>> 0` after every operation that can set bit 31, and
   never use `<<` where the result can exceed 2^31 — use `* 2 ** k` and `>>> 0`.
   Values wider than 32 bits (the range coder's `low`) use `BigInt`, or are split
   into two halves; §8 pins which.
3. **C++ integer promotion.** `uint8_t << 24` promotes to `int` and overflows
   (UB). Cast to `uint32_t` first. `-Werror` catches some of this; it does not
   catch all of it.

### 0.6 What a "golden codec" is

Modules 1, 2, 4 and 9 are transforms or primitives, not compressors. They still
need a byte-in/byte-out codec so that `golden/` can pin them and the 5×5 parity
matrix can exercise them. Each such module below defines its **golden codec** —
a deliberately simple wrapper whose only job is to drive the primitive over real
data on a real byte boundary. Expansion is expected and is not a defect: the deck
says so out loud when it shows the ratio table.

---

## 1. `bitio` — bit writer and bit reader

### 1.1 MSB-first writer

State: `buf: u8 = 0`, `nbits: int = 0` (0..7), output byte list.

```
writeBit(b):            # b is 0 or 1
    buf |= b << (7 - nbits)
    nbits += 1
    if nbits == 8: emit(buf); buf = 0; nbits = 0

writeBits(v, n):        # 0 <= n <= 64, only the low n bits of v are used
    for i in n-1 .. 0:  writeBit((v >> i) & 1)

flush():
    if nbits > 0: emit(buf); buf = 0; nbits = 0
```

**Flush padding is zero bits.** This is the single most common parity break:
an implementation that pads with ones, or that emits a byte even when `nbits == 0`,
produces a file that differs from every other language in the last byte only.

### 1.2 MSB-first reader

State: input bytes, `pos: int`, `buf: u8`, `nbits: int = 0`.

```
readBit() -> 0|1:
    if nbits == 0:
        if pos == len(src): error "bit stream exhausted"
        buf = src[pos]; pos += 1; nbits = 8
    nbits -= 1
    return (buf >> nbits) & 1

readBits(n) -> u64:
    v = 0
    for i in 1..n: v = (v << 1) | readBit()
    return v
```

A reader must not treat the zero padding at the end as data. Every format in this
deck knows how many items to read before it reaches the padding — that is why each
one carries an explicit count or an explicit end marker. Relying on "read until
exhausted" is a defect.

### 1.3 LSB-first writer and reader

Identical, with the bit position mirrored:

```
writeBit(b):  buf |= b << nbits;  nbits += 1;  if nbits == 8: emit
writeBits(v, n):  for i in 0 .. n-1: writeBit((v >> i) & 1)
readBit():    ...;  bit = buf & 1;  buf >>= 1;  nbits -= 1
readBits(n):  v = 0;  for i in 0 .. n-1: v |= readBit() << i;  return v
```

Note that `writeBits` runs low-bit-first here and high-bit-first in §1.1. This is
what RFC 1951 means by "Huffman codes are packed starting with the most significant
bit of the code" while everything else is LSB-first: the *values* go in LSB-first,
the *Huffman codes* go in MSB-first, through the same LSB-first writer. §10 pins it.

### 1.4 Golden codec `bitio`

```
varint(n)                       # original length
then, MSB-first:
    writeBits(0, 3)             # three zero bits — see below
    for each byte b: writeBits(b, 8)
    flush()
```

The three leading zero bits exist on purpose: they push every byte across a byte
boundary, so an implementation that secretly does `memcpy` instead of going through
the bit writer produces a different file. Decoding reads 3 bits, then `n` times 8
bits. Output size is `len(varint(n)) + ceil((3 + 8n) / 8)` — for `n = 0` that is
1 + 1 = **2 bytes**, which is the exception noted in §0.3.

---

## 2. `intcode` — integer codes

All of these are defined on the **MSB-first** bit stream from §1, except `varint`,
which is a byte-level code.

### 2.1 LEB128 unsigned varint (byte-level)

```
varint(v: u64) -> bytes:
    loop:
        b = v & 0x7F;  v >>= 7
        if v != 0: emit(b | 0x80)
        else:      emit(b); return
```

Low 7 bits first, continuation bit 0x80. `varint(0)` is one byte `0x00`.
Maximum length is 10 bytes. A decoder that reads an 11th continuation byte, or
whose accumulated value would exceed `2^64 - 1`, raises an error — it does not
wrap silently.

### 2.2 Zigzag

```
zigzag(n: i64) -> u64:    (n << 1) ^ (n >> 63)      # >> is ARITHMETIC here
unzigzag(u: u64) -> i64:  (u >> 1) ^ -(u & 1)       # >> is LOGICAL here
```

The arithmetic shift is the whole trick, and it is exactly what Java's `>>` gives
and what TypeScript's `>>` on a 32-bit value gives. For 64-bit values in TS use
`BigInt`: `(n << 1n) ^ (n >> 63n)`.

### 2.3 Elias gamma (n >= 1)

```
L = bitlen(n)               # number of bits, so bitlen(1) = 1
writeBits(0, L - 1)         # L-1 zeros
writeBits(n, L)             # n itself, MSB-first, leading 1 included
```

So gamma(1) = `1`, gamma(2) = `010`, gamma(3) = `011`, gamma(4) = `00100`.
Reading: count zeros until the first 1 — that count is `L-1`; the 1 already read is
the top bit of `n`; read `L-1` more bits. **gamma(0) does not exist.** Coding a
value that can be zero means coding `n+1`.

### 2.4 Elias delta (n >= 1)

```
L = bitlen(n)
gamma(L)                    # §2.3
writeBits(n, L - 1)         # n WITHOUT its leading 1
```

delta(1) = `1`, delta(2) = `0100`, delta(3) = `0101`, delta(4) = `01100`.

### 2.5 Golomb–Rice(k), k >= 0 (n >= 0)

```
q = n >> k
r = n & ((1 << k) - 1)
writeBits(all ones, q)      # q one-bits
writeBit(0)                 # terminator
writeBits(r, k)             # k bits, MSB-first; nothing at all when k == 0
```

**Unary is q ones then a zero**, not q zeros then a one. Both conventions are in
the literature; mixing them is a silent parity break because short values still
happen to round-trip within one implementation.

Both sides cap the unary run at **4096** one-bits. Without a cap a corrupt file is
an infinite loop; with a cap that is too small the code becomes useless. 64 was the
first number written here and it was wrong: `Rice(k = 0)` *is* plain unary, which is
how the deck introduces unary coding, and a cap of 64 makes it unable to express
100. 4096 bounds a corrupt stream to 4 Ki iterations per symbol and still covers
every value the deck actually codes.

The **encoder** raises on `q > 4096` too: a caller who picks `k = 0` for a value of
2^40 is asking for a 128 GiB unary run, and silently producing it is worse than
refusing.

### 2.6 Golden codec `intcode`

```
varint(n)
then, MSB-first:
    for each byte b: gamma(b + 1)      # +1 because gamma has no zero
    flush()
```

`b + 1` is in 1..256, so codes are 1 to 17 bits long. On `zeros_64k.bin` every byte
is gamma(1) = one bit, so the body is n/8 bytes — a 8:1 "compression" that is
really just a demonstration that gamma is a unary-ish code. On `random_64k.bin` the
average code is about 15 bits and the file nearly doubles. Both numbers belong in
the deck; neither is a defect.

---

## 3. `rle` — run-length encoding

Two codes live in this module. The golden codec is PackBits (§3.1); `rle0` (§3.2)
exists because bzip2 (module 13) needs it.

### 3.1 PackBits

Stream of *packets*. Each packet is a control byte `c` followed by data:

| `c` | meaning | data |
|---|---|---|
| 0..127 | literal run of `c + 1` bytes | that many bytes |
| 129..255 | repeat of `257 - c` copies (2..128) | one byte |
| 128 | never emitted | — |

The encoder never emits 128; a decoder that meets it raises. (Apple's original
PackBits treats it as a no-op. We do not, because "silently ignore a byte" hides
corruption, and because an encoder that can emit two different byte strings for the
same input cannot have a golden vector.)

**Encoder, exactly:**

```
i = 0
while i < n:
    run = length of the maximal run of equal bytes starting at i, capped at 128
    if run >= 3:
        emit(257 - run); emit(src[i]); i += run
    else:
        # gather literals until a run of >= 3 starts, or 128 bytes, or EOF
        j = i
        while j < n and (j - i) < 128:
            r = length of the maximal run of equal bytes starting at j, capped at 128
            if r >= 3: break
            j = min(j + r, i + 128)        # never let a packet exceed 128 bytes
        emit(j - i - 1); emit(src[i..j]); i = j
```

Pinned choices, all of which change the output bytes:

- **Run threshold is 3.** A run of exactly 2 is emitted as literals. (Encoding it
  as a run costs the same 2 bytes but would make the output depend on what comes
  next, which makes the encoder harder to specify and no smaller.)
- **Run cap is 128**, literal cap is 128.
- A literal packet is ended by the *start* of a run of 3, not by the run being
  long. The inner loop advances by whole equal-byte groups so that a group of 2
  never gets split across packets — except at the 128-byte cap, where the group is
  split, because the cap is the harder constraint. `min(j + r, i + 128)` is that
  rule; dropping the `min` gives 129-byte packets on some inputs, and a packet
  length that does not fit the control byte is a file no one can decode.

**Header:** `varint(n)` then the packets. The decoder stops when it has produced
`n` bytes; trailing bytes after that are an error.

### 3.2 `rle0` — zero-run coding

Used between MTF and Huffman in bzip2, where the MTF output is mostly zeros.
Runs of zeros are coded in bijective base 2 with digits RUNA=0 and RUNB=1:

```
a run of L zeros (L >= 1):
    L += 1
    while L > 1:
        emit RUNA if (L & 1) == 0 else RUNB
        L >>= 1
```

Non-zero MTF symbol `s` is emitted as `s + 1`. Symbol 0 and 1 are therefore RUNA
and RUNB, and the alphabet grows by one. This is bzip2's exact scheme; it is
specified here so module 13 does not have to re-derive it, and it is **not** part
of the `rle` golden codec.

---

## 4. `mtf` — move-to-front

Alphabet is the 256 byte values. The table starts as the identity: `t[i] = i`.

```
encode(src):
    t = [0,1,...,255]
    for b in src:
        i = index of b in t
        emit(i)
        move t[i] to the front (shifting t[0..i-1] up by one)

decode(src):
    t = [0,1,...,255]
    for i in src:
        b = t[i]; emit(b)
        move t[i] to the front
```

The move is a rotation, not a swap. A swap is a different (and worse) transform
that still round-trips inside one implementation — another silent parity break.

Complexity is O(n·256) worst case with the straightforward list. That is fine at
our sizes and it is what all five implementations do, so that the code the deck
shows is the code that produced the numbers. The deck's BWT chapter discusses the
faster variants without implementing them.

### 4.1 Golden codec `mtf`

`varint(n)` then the `n` transformed bytes. Output is always `len(varint(n)) + n`.

---

## 5. `huffman` — canonical, length-limited Huffman

### 5.1 Code lengths: package–merge, limit 15

Building a Huffman tree by repeatedly joining the two lightest nodes gives optimal
lengths but **not** deterministic ones: the tie-breaking inside the priority queue
differs between languages, and two different length vectors can both be optimal.
So we do not build a tree. We compute the length vector directly with
package–merge, whose output is a function of the frequency vector alone.

Let `S` be the symbols with `freq > 0`, sorted ascending by `(freq, symbol)`.
Let `m = |S|` and `L = 15`.

```
if m == 0: no lengths at all (only possible when n == 0)
if m == 1: that symbol gets length 1; stop.

I = [ coin(weight = freq(s), kind = SYMBOL, rank = j) for j, s in enumerate(S) ]
P = I
repeat L - 1 times:
    Q = package(P)          # [P[0]+P[1], P[2]+P[3], ...], drop a trailing odd item
    P = merge(Q, I)         # stable ascending merge, see key below
take the first (2m - 2) items of P
length(s) = number of times symbol s occurs among those items
```

`package` sums weights and concatenates the symbol multisets.
`merge` sorts ascending by the key `(weight, kind, rank)` where `kind` is 0 for a
coin from `I` and 1 for a package, and `rank` is the coin's index in `I` or the
package's index in `Q`. **That key is the entire tie-breaking rule.** With it,
package–merge is a pure function of the frequency vector and all five languages
produce the same lengths without sorting stability being a shared assumption.

The result always satisfies the Kraft equality, so no fix-up pass is needed. The
deck shows the fix-up loop that DEFLATE implementations usually carry (zlib's
`gen_bitlen` overflow repair) as an alternative, and says why we do not need it.

Complexity: O(L · m log m) time, O(L · m) space — 15 · 256 coins at most, which is
why the simple formulation is affordable here and why a real DEFLATE encoder,
running this per block, uses the cheaper repair loop instead.

### 5.2 Canonical code assignment

Given the lengths, codes are assigned exactly as RFC 1951 §3.2.2 does:

```
bl_count[l] = number of symbols with length l   (bl_count[0] = 0)
code = 0
for bits in 1 .. 15:
    code = (code + bl_count[bits - 1]) << 1
    next_code[bits] = code
for sym in 0 .. 255 ascending:
    if length[sym] != 0:
        code[sym] = next_code[length[sym]]
        next_code[length[sym]] += 1
```

So codes are ordered by `(length ascending, symbol ascending)` — the tie-break the
plan names. Codes are written **MSB-first**: a code of length `l` and value `c` is
`writeBits(c, l)` on the §1.1 writer.

### 5.3 Golden codec `huffman`

```
varint(n)
if n == 0: stop                           # encode(b"") is the single byte 0x00
128 bytes: code lengths, 4 bits each
          byte i holds symbol 2i in the HIGH nibble and symbol 2i+1 in the LOW nibble
          length 0 means "symbol does not occur"
MSB-first bit stream: the code for each of the n input bytes, then flush()
```

The header is a fixed 128 bytes even when three symbols are used. It is the
simplest header that cannot be ambiguous, and part 4 of the deck uses it as the
starting point for "how does DEFLATE make this header smaller?" — which is exactly
what the dynamic block's code-length alphabet (§10.5) is for.

**Single-symbol input.** `abab_4k.txt` is not this case, but `zeros_64k.bin` is:
one symbol, length 1, code `0`. The body is `n` zero bits. A decoder must handle a
one-symbol table without dividing by zero or looping — it reads one bit per symbol.

**Decoding** uses a canonical decoder, not a tree: keep `first_code[l]`,
`first_index[l]` and the symbol list sorted by `(length, symbol)`; read bits one at
a time accumulating `code`, and at each length `l` test `code - first_code[l] <
count[l]`. O(1) memory, O(code length) per symbol, and no tree to build — so the
five implementations cannot disagree about tree shape.

---

## 6. `lzss` — LZ77 with a 32 KiB window

### 6.1 Parameters (all pinned)

| Name | Value |
|---|---|
| window | 32768 bytes |
| min match | 3 |
| max match | 258 |
| hash | over exactly 3 bytes |
| hash function | `h = ((b0 << 10) ^ (b1 << 5) ^ b2) & 0x7FFF` |
| hash table | 32768 buckets, `head[h]` = most recent position, `-1` if none |
| chain | `prev[pos & 32767]` = previous position with the same hash |
| chain limit | 32 probes per position |
| parse | greedy (lazy matching is DEFLATE's, §10.4) |
| tie-break | longest wins; on equal length the **nearest** (smallest distance) wins |

**The chain array is indexed by absolute position, not by `pos & 32767`.** zlib
wraps it into a window-sized array, and that is exactly why zlib's effective maximum
distance is `32768 - 262 = 32506`: the slot for `pos - 32768` has already been
overwritten by `pos`. Ours costs O(n) memory instead of O(window) and can actually
reach distance 32768 — which is what `corpus/boundary_32768.bin` checks, and what
part 7 of the deck compares against real gzip.

The chain is walked from the most recent position backwards, and a candidate
replaces the incumbent only when it is **strictly longer**. That is what makes
"nearest on a tie" fall out for free, and it is the reason the comparison must be
`>` and not `>=`. A `>=` gives a valid file that decodes correctly and has a
different SHA-256 — the single most likely parity break in this module.

Positions within `min match - 1` of the end cannot start a match.
A match may overlap itself: `dist = 1, len = 100` is legal and means "repeat the
previous byte 100 times". The decoder must copy **byte by byte**, forwards; a
`memmove` is wrong here.

### 6.2 Token stream

Items are grouped in eights. Each group is one flag byte followed by its items.

```
flag byte: bit 7 is the first item of the group, bit 0 the eighth
           1 = match, 0 = literal
literal:   1 byte
match:     u8  (len - 3)        # 0..255  -> len 3..258
           u16le (dist - 1)     # 0..32767 -> dist 1..32768
```

A final partial group still writes a full flag byte; the unused low bits are zero.

### 6.3 Container

```
varint(n)
groups...
```

The decoder stops when it has produced `n` bytes and must not read further; a
stream with trailing bytes is an error.

---

## 7. `lzw` — LZ78 with a growing dictionary

### 7.1 Parameters

| Name | Value |
|---|---|
| initial code width | 9 bits |
| maximum code width | 12 bits |
| `CLEAR` | 256 |
| `EOF` | 257 |
| first free code | 258 |
| dictionary cap | 4096 entries |
| bit order | MSB-first |

### 7.2 Encoder

```
reset():  next_free = 258;  width = 9;  dict = {}      # single bytes are implicit
w = empty
for each byte k in src:
    if w is empty:              w = [k];  continue
    if (w, k) in dict:          w = w + [k];  continue
    emit(code(w), width)
    if next_free == 4096:
        emit(CLEAR, width);  reset()
    else:
        dict[(w, k)] = next_free;  next_free += 1
        if next_free == (1 << width) and width < 12:  width += 1
    w = [k]
if w is not empty: emit(code(w), width)
emit(EOF, width)
flush()
```

Two details that are the whole specification:

- The width check happens **after** adding the entry and therefore applies to the
  *next* code emitted, not this one.
- `CLEAR` is emitted at the moment the dictionary is full, **in place of** adding
  the 4096th entry, and it is emitted at the width in force at that moment (12).
  After it, width is 9 again.

### 7.3 Decoder — and the one-step lag

The decoder learns each dictionary entry one code later than the encoder creates
it. At the point the encoder is about to emit code *i*, the encoder's `next_free`
has already counted *i−1* additions; the decoder, about to read code *i*, has only
made *i−2* additions. It is one behind. So the decoder's width rule is shifted by
one:

```
reset():  next_free = 258;  width = 9;  prev = none
loop:
    c = readBits(width)
    if c == EOF:   break
    if c == CLEAR: reset();  continue
    if prev is none:
        entry = [c]                       # c must be < 256
    elif c < next_free:
        entry = dict[c]
    elif c == next_free:
        entry = prev + [prev[0]]          # the KwKwK case
    else:
        error "code from the future"
    output(entry)
    if prev is not none:
        dict[next_free] = prev + [entry[0]];  next_free += 1
    prev = entry
    if next_free + 1 == (1 << width) and width < 12:  width += 1
```

`next_free + 1` — not `next_free` — is the lag correction. Getting it wrong
produces a decoder that works for small files and desynchronises at exactly 254
dictionary entries, which is why `corpus/abab_4k.txt` and `corpus/english.txt` both
have to be in the golden set.

The `c == next_free` branch is the classic KwKwK case (input `ababab…`): the
encoder used an entry the decoder has not built yet, and the entry is always
`prev + prev[0]`. `corpus/abab_4k.txt` exists to force it.

### 7.4 Container

`varint(n)` then the MSB-first code stream. `n` is redundant with `EOF` and both
are checked: a stream whose `EOF` arrives at the wrong output length is an error.
The redundancy is deliberate — the deck uses it to show that a real format
(`.Z`, GIF) has no such cross-check and what that costs.

---

## 8. `rangecoder` — binary range coder with adaptive models

This is the LZMA range coder, unchanged, because module 14 (`lzmadec`) has to
decode real `.lzma` files and a second coder would be two things to get right.

### 8.1 Constants

| Name | Value |
|---|---|
| `PROB_BITS` | 11 |
| `PROB_TOTAL` | 2048 (`1 << PROB_BITS`) |
| `PROB_INIT` | 1024 (probability 1/2) |
| `MOVE_BITS` | 5 |
| `TOP` | 2^24 |
| initial `range` | 0xFFFFFFFF |

A probability is a `u16` in 1..2047 holding P(bit = 0) scaled by 2048.

### 8.2 Encoder

State: `low: u64` (never exceeds 2^33), `range: u32`, `cache: u8 = 0`,
`cacheSize: u64 = 1`.

```
shiftLow():
    if (low >> 32) != 0 or low < 0xFF000000:
        temp = cache
        repeat:
            emit((temp + (low >> 32)) & 0xFF)
            temp = 0xFF
            cacheSize -= 1
        until cacheSize == 0
        cache = (low >> 24) & 0xFF
    cacheSize += 1
    low = (low << 8) & 0xFFFFFFFF

encodeBit(prob[], i, bit):
    bound = (range >> PROB_BITS) * prob[i]
    if bit == 0:
        range = bound
        prob[i] += (PROB_TOTAL - prob[i]) >> MOVE_BITS
    else:
        low   += bound
        range -= bound
        prob[i] -= prob[i] >> MOVE_BITS
    while range < TOP:
        range = (range << 8) & 0xFFFFFFFF
        shiftLow()

flush():
    repeat 5 times: shiftLow()
```

Because `cache` starts at 0 and `cacheSize` at 1, **the first byte of every range
coder stream is 0x00.** It carries no information; it is the place a carry out of
the first real byte would have landed. The decoder skips it. This is not a quirk we
invented — real `.lzma` files start with it, and module 14 depends on it.

### 8.3 Decoder

```
init():
    range = 0xFFFFFFFF
    code  = 0
    skip one byte (it must be 0x00, else error)
    repeat 4 times: code = ((code << 8) | readByte()) & 0xFFFFFFFF

decodeBit(prob[], i) -> 0|1:
    bound = (range >> PROB_BITS) * prob[i]
    if code < bound:
        range = bound
        prob[i] += (PROB_TOTAL - prob[i]) >> MOVE_BITS
        bit = 0
    else:
        code  -= bound
        range -= bound
        prob[i] -= prob[i] >> MOVE_BITS
        bit = 1
    while range < TOP:
        range = (range << 8) & 0xFFFFFFFF
        code  = ((code << 8) | readByte()) & 0xFFFFFFFF
    return bit
```

When the encoder's stream runs out, a decoder that still needs bytes reads 0x00.
(A real decoder must not, and ours checks; but the last `decodeBit` of a well-formed
stream can legitimately pull one byte past the last informative one, so the check is
"more than 5 bytes past the end is an error".)

### 8.4 Per-language notes for §8

- **Java:** `low` is `long`; `range`, `code` and `bound` are `int` used as unsigned —
  compare with `Integer.compareUnsigned`, shift with `>>>`. `(range >>> 11) * prob`
  must be computed as `long` or it overflows `int`; store back with a cast.
- **TypeScript:** `low`, `range`, `code` and `bound` are plain numbers. Every one of
  them stays below 2^33, which is exact in a double, so **no BigInt is needed** —
  but `<<` is forbidden on them (it coerces to signed 32-bit). Use
  `range = (range * 256) % 0x100000000` and `Math.floor(range / 2048)`.
  `>>>` is safe and is used where the value is known to be below 2^32.
- **C++:** `low` is `uint64_t`, the rest `uint32_t`. `(range >> 11) * prob` is
  `uint32_t * uint16_t` promoted to `int` — cast `prob` to `uint32_t` first.
- **Go:** `low uint64`, rest `uint32`. Nothing special; Go is the reference shape.
- **Python:** everything is a big integer, so every assignment to `low`, `range`
  and `code` must be masked with `& 0xFFFFFFFF` (or `& 0x1FFFFFFFF` for `low`)
  explicitly. Python is the language most likely to be silently wrong here,
  because nothing overflows to tell you.

### 8.5 Order-0 adaptive byte model

256 probabilities in a single array, used as a binary tree; index 0 is unused.

```
encodeByte(probs[256], b):
    ctx = 1
    for i in 7 .. 0:
        bit = (b >> i) & 1
        encodeBit(probs, ctx, bit)
        ctx = (ctx << 1) | bit        # ends at 256..511, discarded

decodeByte(probs[256]) -> b:
    ctx = 1
    repeat 8 times:
        ctx = (ctx << 1) | decodeBit(probs, ctx)
    return ctx - 256
```

`ctx` reaches 256..511 on the last step, so only indices 1..255 are ever passed to
`encodeBit` — the array is 256 entries and index 0 is never used. All entries start
at `PROB_INIT`.

### 8.6 Golden codec `rangecoder`

```
varint(n)
range coder stream: n bytes through one shared order-0 model, then flush()
```

---

## 9. `bwt` — Burrows–Wheeler transform

### 9.1 Block format

```
varint(n)                       # total original length
per block, in order:
    u32le primary                # row index of the original rotation
    block_len bytes              # the L column
```

`block_len` is 65536 for every block but the last, which is `n mod 65536` (and
there is no last block when that is 0). Block length is therefore derivable from
`n` and is not stored. The 900 KiB blocks that real bzip2 uses appear in module 13,
not here.

If `n == 0` the output is the single byte `0x00`.

### 9.2 Forward transform

Sort all `m` rotations of the block; `L[i]` is the last character of the `i`-th
sorted rotation; `primary` is the position in that sorted order of the rotation
that starts at offset 0.

The sort is done by **suffix doubling on the doubled block**: ranks of
length-1 prefixes, then 2, 4, 8 … until all ranks are distinct or `k >= m`.
O(m log² m) time, O(m) space.

**Ties.** When two rotations are identical (`zeros_64k.bin`: all 65536 rotations
are equal), the doubling never separates them. The order among equal rotations is
then **ascending by starting offset**, which is what a stable sort on the initial
rank array gives for free — and it must be stated, because an unstable sort gives a
different `primary` and a different golden vector, while still inverting correctly.

### 9.3 Inverse transform (LF mapping)

```
count[c] = number of occurrences of c in L
first[c] = sum of count[c'] for c' < c          # position of c's first row
next[i]  = first[L[i]] + (number of L[j] == L[i] for j < i)
```

Then walk: `i = primary`, and `m` times output `L[i]`, `i = next[i]` — this
produces the original **backwards**, so the standard formulation inverts the walk.
We use the forward-producing variant instead:

```
T[j] for j in 0..m-1: the row whose L character is the j-th occurrence,
                      i.e. the inverse permutation of next
i = primary
for k in 0 .. m-1:
    i = T[i]
    output(L[i])
```

Both are correct; the second is pinned because it is the one the deck draws, and
because reversing a 64 KiB buffer afterwards is an allocation the C++ and Go
versions would rather not make. O(m) time, O(m + 256) space.

### 9.4 Golden codec `bwt`

The container of §9.1. Output length is `len(varint(n)) + n + 4 · number_of_blocks`.
BWT alone never compresses; the deck shows its output next to the MTF+RLE0+Huffman
pipeline of part 10 so that the reader sees where the gain actually comes from.

---

## 10. `deflate` — the real thing (RFC 1951), plus zlib and gzip

This module is the only one in Tier 1 that implements someone else's format rather
than one of ours, so the specification is RFC 1951 / 1950 / 1952 and this section
only pins **the choices the RFC leaves to the encoder**. Those choices are what
make our output byte-identical across five languages — and they are also why our
output is not byte-identical to `gzip -9`. The contract with the real tools is
weaker and is stated in §10.9.

### 10.1 Bit order — the exception in this deck

DEFLATE is **LSB-first** (§1.3) for everything *except* Huffman codes, which are
packed most-significant-bit-first through the same LSB-first writer. Concretely:

```
putBits(value, n)        # header fields, extra bits: LSB-first
putCode(code, len)       # Huffman code: for i in len-1 .. 0: writeBit((code >> i) & 1)
```

### 10.2 Block layout

```
BFINAL  1 bit    1 on the last block
BTYPE   2 bits   00 stored, 01 fixed Huffman, 10 dynamic Huffman, 11 invalid
```

- **Stored (00):** discard bits to the next byte boundary, then `u16le LEN`,
  `u16le NLEN = LEN ^ 0xFFFF`, then `LEN` raw bytes. `LEN <= 65535`.
- **Fixed (01):** the fixed code tables of RFC 1951 §3.2.6.
- **Dynamic (10):** §10.5.

Every non-stored block ends with the end-of-block symbol 256.

### 10.3 Length and distance codes

The tables are generated once by `tools/gen_tables.py` into all five languages, so
they cannot drift. They are reproduced here as the authority.

Length codes 257..285 — `(code, extra bits, base length)`:

```
257,0,3   258,0,4   259,0,5   260,0,6   261,0,7   262,0,8   263,0,9   264,0,10
265,1,11  266,1,13  267,1,15  268,1,17
269,2,19  270,2,23  271,2,27  272,2,31
273,3,35  274,3,43  275,3,51  276,3,59
277,4,67  278,4,83  279,4,99  280,4,115
281,5,131 282,5,163 283,5,195 284,5,227
285,0,258
```

Code 284 can express 227..257 only; **length 258 is always code 285**, never
`284 + 31`. (Both decode correctly; only one is what every real encoder emits, and
picking the other would make our streams odd without making them shorter.)

Distance codes 0..29 — `(code, extra bits, base distance)`:

```
0,0,1     1,0,2     2,0,3     3,0,4
4,1,5     5,1,7     6,2,9     7,2,13
8,3,17    9,3,25    10,4,33   11,4,49
12,5,65   13,5,97   14,6,129  15,6,193
16,7,257  17,7,385  18,8,513  19,8,769
20,9,1025 21,9,1537 22,10,2049 23,10,3073
24,11,4097 25,11,6145 26,12,8193 27,12,12289
28,13,16385 29,13,24577
```

Distance codes 30 and 31 exist in the alphabet but are never valid in a stream.

Fixed tables (BTYPE 01): literals 0..143 are 8 bits (codes 0x30..0xBF), 144..255
are 9 bits (0x190..0x1FF), 256..279 are 7 bits (0x00..0x17), 280..287 are 8 bits
(0xC0..0xC7). Distances are 5 bits each, values 0..29 coded as 0..29.

### 10.4 Our encoder's parse

Same hash chain as §6.1 (3-byte hash, 32768 buckets), with these differences,
all pinned:

| Name | Value |
|---|---|
| chain limit | 128 probes |
| `nice_length` | 258 — stop searching as soon as a match this long is found |
| lazy matching | on |
| lazy rule | having a match of length `L` at `i`, look for a match at `i+1`; if its length is **strictly greater** than `L`, emit `src[i]` as a literal and re-decide at `i+1` |
| min match | 3 |
| max match | 258 |
| max distance | 32768 |

No `good_match` heuristic, no "reduce chain length once the match is long enough":
zlib has those and they are what makes zlib's output depend on its compression
level. Ours has one behaviour, and the deck compares its ratio with `gzip -9`'s in
part 9 rather than pretending to match it.

### 10.5 Dynamic block header

```
HLIT   5 bits   number of lit/len codes - 257   (we always send exactly what is used)
HDIST  5 bits   number of distance codes - 1
HCLEN  4 bits   number of code-length codes - 4
then HCLEN + 4 groups of 3 bits, in this order:
    16,17,18,0,8,7,9,6,10,5,11,4,12,3,13,2,14,1,15
then the lit/len and distance code lengths, run-length coded with the
code-length alphabet:
    0..15  a literal code length
    16     copy the previous length 3..6 times   (2 extra bits, base 3)
    17     repeat length 0 for 3..10 times       (3 extra bits, base 3)
    18     repeat length 0 for 11..138 times     (7 extra bits, base 11)
```

Pinned encoder choices inside the header:

- `HLIT` is `max(257, highest used lit/len symbol + 1)`; `HDIST` is
  `max(1, highest used distance symbol + 1)`. When no match was emitted at all,
  one distance code is still sent, with length 1, and never used.
- `HCLEN` is trimmed: trailing zero entries of the permuted code-length-code
  length array are dropped, down to a minimum of 4.
- The run-length coder is greedy and left to right: at each position take the
  longest applicable of 18, 17, 16, else the literal length. Code 16 may only
  follow an already-emitted length.
- All three Huffman tables use the §5.1 package–merge with limit 15 (7 for the
  code-length alphabet, per the RFC).

### 10.6 Block splitting and type choice

- The encoder consumes the input in blocks of at most **65536 bytes**.
- For each block it computes the exact bit cost of all three forms and picks the
  smallest. **On a tie the order of preference is stored, then fixed, then
  dynamic.** Both the tie rule and the exactness matter: an estimate that is off by
  one bit changes the chosen type on some corpus file, and then the golden vector
  depends on which language's estimate rounded which way.
- A stored block's cost is `3 + padding-to-byte + 32 + 8·len` bits, where the
  padding depends on the current bit position — so block type choice is not a pure
  function of the block contents. It is still deterministic, because the encoder
  processes blocks strictly in order.
- `encode(b"")` is one final fixed block containing only the end-of-block symbol.
  That is 1 + 2 + 7 = 10 bits — `BFINAL=1`, `BTYPE=01` (LSB-first, so bits 1,1,0),
  then code 256 as seven zero bits — which flushes to the **two bytes `03 00`**.
  The exact bytes are pinned by the golden vector for `empty.bin`.

### 10.7 Inflate

A full RFC 1951 decoder: all three block types, canonical decoding built from code
lengths (the §5.2 construction, LSB-first reading), the 32 KiB sliding window as a
flat growing output buffer, and byte-by-byte copying for overlapping matches.

It must reject, rather than tolerate: `BTYPE == 11`; `NLEN != LEN ^ 0xFFFF`; an
over-subscribed or incomplete code table (the one exception RFC 1951 allows is a
distance table with a single code, which we accept); a distance greater than the
bytes produced so far; code-length code 16 appearing first; a repeat that runs past
the end of the length array.

### 10.8 Containers

**zlib (RFC 1950):**

```
CMF  = 0x78          # CM=8 (deflate), CINFO=7 (32 KiB window)
FLG  = 0x9C          # FDICT=0, FLEVEL=2, and (CMF<<8 | FLG) % 31 == 0
<deflate stream>
u32be Adler-32 of the uncompressed data
```

Adler-32: `a = 1, b = 0`; for each byte `a = (a + byte) % 65521`,
`b = (b + a) % 65521`; result `(b << 16) | a`. The modulus may be deferred but must
be applied at least every 5552 bytes.

**gzip (RFC 1952):**

```
1f 8b 08 00          # magic, CM=8, FLG=0
00 00 00 00          # MTIME = 0 — fixed, so our output is reproducible
00 ff                # XFL=0, OS=255 (unknown)
<deflate stream>
u32le CRC-32 of the uncompressed data
u32le ISIZE = original length mod 2^32
```

`MTIME = 0` and `OS = 255` are chosen so that `make record` run three times
produces identical bytes. Real `gzip` writes the file's mtime and the host OS, so
its output is *not* reproducible — the deck says so, with the capture.

CRC-32: the reflected polynomial 0xEDB88320, initial value 0xFFFFFFFF, final XOR
0xFFFFFFFF. The 256-entry table comes from `tools/gen_tables.py`.

### 10.9 What "interop" means here

Two different contracts, and the deck must not blur them:

- **Both directions must work.** `gzip -d` decompresses our gzip output; our
  inflate decompresses `gzip`'s, `gzip -1`'s and `gzip -9`'s output, and Python's
  `zlib.decompress` accepts our zlib stream while our inflate accepts
  `zlib.compress` at every level 0..9. All of this is captured into
  `out/interop_deflate_*.txt`.
- **Bytes are not expected to match.** Our encoder makes different (simpler)
  choices than zlib. Any claim in the deck that our output equals a real tool's
  output would be false, and there is no such claim.

---

## 11. Summary — what each golden codec produces

| Module | Container | `encode(b"")` | Compresses? |
|---|---|---|---|
| `bitio` | `varint(n)` + 3 pad bits + 8n bits | `00 00` | no — grows by 1 byte per 21 |
| `intcode` | `varint(n)` + gamma(b+1) stream | `00` | only on low-entropy bytes |
| `rle` | `varint(n)` + PackBits packets | `00` | on runs only |
| `mtf` | `varint(n)` + n bytes | `00` | never — it is a permutation |
| `huffman` | `varint(n)` + 128-byte table + codes | `00` | yes, to order-0 entropy |
| `lzss` | `varint(n)` + flag groups | `00` | yes |
| `lzw` | `varint(n)` + 9..12-bit codes | `00` | yes |
| `rangecoder` | `varint(n)` + rc stream | `00` | yes, below Huffman |
| `bwt` | `varint(n)` + (u32le primary + block)* | `00` | never — it is a permutation |
| `deflate` | raw RFC 1951 stream | `03 00` | yes |

`bitio` and `deflate` are the two whose empty output is not `00`: `bitio` because
its three pad bits still need a byte, `deflate` because it is the one module whose
container we did not choose.

## 12. Error handling contract

Every decoder validates before it allocates and before it indexes:

1. `varint` that does not terminate within 10 bytes, or whose value exceeds
   `2^32 - 1` for a length field → error. (We cap decoded lengths at 4 GiB so that
   a corrupt header cannot ask a 32-bit platform for an impossible allocation.)
2. Reading past the end of the input → error, never a silent zero.
3. A produced length that disagrees with the header's `n` → error.
4. A back-reference pointing before the start of the output → error.
5. Unary or run-length loops bounded explicitly (§2.5, §3.1) so that corrupt input
   terminates.

`tests/` in every language contains the same eight malformed inputs (truncated
header, truncated body, length field too large, distance too large, code from the
future, PackBits control 128, over-subscribed Huffman table, `NLEN` mismatch) and
asserts that each one raises rather than crashes or hangs.
