package compresslib;

/**
 * ANS — 비대칭 수 체계 — SPEC §13.
 *
 * <p>rANS 는 <b>스택</b> 이다. 부호기가 입력을 뒤에서부터 밀어 넣고
 * 복호기가 앞에서부터 꺼낸다.
 *
 * <p>상태 x 는 (x / f) * TOTAL 에서 2^31 에 닿는다. 자바에는 부호 없는
 * int 가 없으므로 x 를 long 에 담고 곱셈·나눗셈을 쓴다 (SPEC §0.5).
 */
public final class Ans {
  public static final int TOTAL_BITS = 12;
  public static final int TOTAL = 1 << TOTAL_BITS;
  public static final long L = 1L << 23;
  public static final int ALPHABET = 256;
  /**
   * tANS 의 퍼뜨리기 걸음 (zstd 의 값). 홀수라서 2의 거듭제곱 칸을
   * 빠짐없이 한 번씩 돈다.
   */
  public static final int SPREAD_STEP = (TOTAL >> 1) + (TOTAL >> 3) + 3;

  private Ans() {}

  /**
   * 빈도를 합이 정확히 TOTAL 이 되게 고친다 (SPEC §13.3). 남으면 가장
   * 큰 기호에 한꺼번에, 모자라면 거기서 되풀이해 뺀다. 동점이면
   * 작은 번호.
   */
  public static int[] normalise(long[] counts) {
    long total = 0;
    for (long c : counts) {
      total += c;
    }
    int[] f = new int[ALPHABET];
    if (total == 0) {
      return f;
    }
    for (int s = 0; s < ALPHABET; s++) {
      if (counts[s] > 0) {
        long v = counts[s] * TOTAL / total;
        f[s] = (int) Math.max(1, v);
      }
    }
    long sum = 0;
    for (int v : f) {
      sum += v;
    }
    long d = TOTAL - sum;
    while (d != 0) {
      int best = 0;
      for (int s = 1; s < ALPHABET; s++) {
        if (f[s] > f[best]) {
          best = s;
        }
      }
      if (d > 0) {
        f[best] += (int) d;
        d = 0;
      } else {
        long take = Math.min(-d, f[best] - 1L);
        if (take == 0) {
          throw new CodecException("빈도를 TOTAL 에 못 맞춘다");
        }
        f[best] -= (int) take;
        d += take;
      }
    }
    return f;
  }

  public static int[] cumulative(int[] f) {
    int[] cum = new int[ALPHABET];
    int total = 0;
    for (int s = 0; s < ALPHABET; s++) {
      cum[s] = total;
      total += f[s];
    }
    return cum;
  }

  public static byte[] slotSymbols(int[] f, int[] cum) {
    byte[] slots = new byte[TOTAL];
    for (int s = 0; s < ALPHABET; s++) {
      for (int i = cum[s]; i < cum[s] + f[s]; i++) {
        slots[i] = (byte) s;
      }
    }
    return slots;
  }

  /** tANS 의 상태표 (SPEC §13.6). 골든에는 안 들어가고 12부가 쓴다. */
  public static byte[] tansTable(int[] f) {
    byte[] table = new byte[TOTAL];
    int pos = 0;
    for (int s = 0; s < ALPHABET; s++) {
      for (int i = 0; i < f[s]; i++) {
        table[pos] = (byte) s;
        pos = (pos + SPREAD_STEP) & (TOTAL - 1);
      }
    }
    return table;
  }

  public static byte[] encode(byte[] src) {
    if (src.length == 0) {
      return Varint.put(0);
    }
    long[] counts = new long[ALPHABET];
    for (byte b : src) {
      counts[b & 0xFF]++;
    }
    int[] f = normalise(counts);
    int[] cum = cumulative(f);

    ByteBuf body = new ByteBuf();
    long x = L;
    // 뒤에서부터 민다. rANS 는 스택이라 마지막 것이 먼저 나온다.
    for (int i = src.length - 1; i >= 0; i--) {
      int s = src[i] & 0xFF;
      long fs = f[s];
      long xmax = (L >>> TOTAL_BITS) * 256 * fs;
      while (x >= xmax) {
        body.push((int) (x & 0xFF));
        x >>>= 8;
      }
      x = (x / fs) * TOTAL + (x % fs) + cum[s];
    }
    for (int i = 0; i < 4; i++) {
      body.push((int) ((x >>> (8 * i)) & 0xFF));
    }
    byte[] rev = body.bytes();
    for (int i = 0, j = rev.length - 1; i < j; i++, j--) {
      byte t = rev[i];
      rev[i] = rev[j];
      rev[j] = t;
    }

    ByteBuf out = new ByteBuf();
    Varint.put(out, src.length);
    for (int s = 0; s < ALPHABET; s++) {
      Varint.put(out, f[s]);
    }
    out.extend(rev);
    return out.bytes();
  }

  public static byte[] decode(byte[] src) {
    int[] h = Varint.getLength(src, 0);
    int n = h[0];
    int pos = h[1];
    if (n == 0) {
      if (pos != src.length) {
        throw new CodecException("빈 입력인데 뒤에 바이트가 있다");
      }
      return new byte[0];
    }
    int[] f = new int[ALPHABET];
    long sum = 0;
    for (int s = 0; s < ALPHABET; s++) {
      long[] r = Varint.get(src, pos);
      pos = (int) r[1];
      if (r[0] > TOTAL) {
        throw new CodecException("빈도가 TOTAL 을 넘는다");
      }
      f[s] = (int) r[0];
      sum += r[0];
    }
    if (sum != TOTAL) {
      throw CodecException.of("빈도의 합이 %d 가 아니다", TOTAL);
    }
    int[] cum = cumulative(f);
    byte[] slots = slotSymbols(f, cum);

    if (src.length - pos < 4) {
      throw new CodecException("rANS 스트림이 너무 짧다");
    }
    long x = 0;
    for (int i = 0; i < 4; i++) {
      x = (x << 8) | (src[pos + i] & 0xFF);
    }
    int at = pos + 4;
    byte[] out = new byte[n];
    for (int k = 0; k < n; k++) {
      int slot = (int) (x & (TOTAL - 1));
      int s = slots[slot] & 0xFF;
      out[k] = (byte) s;
      x = (long) f[s] * (x >>> TOTAL_BITS) + slot - cum[s];
      while (x < L) {
        if (at >= src.length) {
          throw new CodecException("rANS 스트림이 모자란다");
        }
        x = (x << 8) | (src[at++] & 0xFF);
      }
    }
    if (at != src.length) {
      throw new CodecException("뒤에 남은 바이트가 있다");
    }
    return out;
  }
}
