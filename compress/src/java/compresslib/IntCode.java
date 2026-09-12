package compresslib;

/**
 * 정수 부호 — SPEC §2.
 *
 * <p>varint 만 바이트 단위이고 감마·델타·라이스는 비트 스트림(MSB
 * 먼저)에서 돈다. 단항은 <b>1 을 q개 쓰고 0 으로 닫는다</b> — 반대
 * 약속도 문헌에 흔한데, 섞어 쓰면 작은 값은 그대로 왕복돼서 골든 벡터
 * 전에는 안 보인다.
 */
public final class IntCode {
  /** 단항 상한 (SPEC §2.5). k=0 인 라이스가 쓸모 있을 만큼은 크게. */
  public static final long MAX_UNARY = 4096;

  private IntCode() {}

  public static long zigzag(long n) {
    return (n << 1) ^ (n >> 63);
  }

  public static long unzigzag(long u) {
    return (u >>> 1) ^ -(u & 1);
  }

  public static int bitLength(long v) {
    return 64 - Long.numberOfLeadingZeros(v);
  }

  public static void putGamma(BitIO.MsbWriter w, long v) {
    if (v < 1) {
      throw CodecException.of("gamma 는 1 이상만: %d", v);
    }
    int n = bitLength(v);
    w.writeBits(0, n - 1);
    w.writeBits(v, n);
  }

  public static long getGamma(BitIO.MsbReader r) {
    int n = 1;
    while (r.readBit() == 0) {
      if (++n > 64) {
        throw new CodecException(
            "gamma 의 길이 부분이 64비트를 넘는다");
      }
    }
    return (1L << (n - 1)) | r.readBits(n - 1);
  }

  public static void putDelta(BitIO.MsbWriter w, long v) {
    if (v < 1) {
      throw CodecException.of("delta 는 1 이상만: %d", v);
    }
    int n = bitLength(v);
    putGamma(w, n);
    w.writeBits(v, n - 1);
  }

  public static long getDelta(BitIO.MsbReader r) {
    long n = getGamma(r);
    if (n > 64) {
      throw new CodecException("delta 의 길이 부분이 64비트를 넘는다");
    }
    return (1L << (n - 1)) | r.readBits((int) n - 1);
  }

  public static void putRice(BitIO.MsbWriter w, long v, int k) {
    long q = v >>> k;
    if (q > MAX_UNARY) {
      throw CodecException.of("rice 의 몫이 %d — k 를 잘못 골랐다", q);
    }
    for (long i = 0; i < q; i++) {
      w.writeBit(1);
    }
    w.writeBit(0);
    if (k > 0) {
      w.writeBits(v & ((1L << k) - 1), k);
    }
  }

  public static long getRice(BitIO.MsbReader r, int k) {
    long q = 0;
    while (r.readBit() == 1) {
      if (++q > MAX_UNARY) {
        throw CodecException.of("rice 의 단항이 %d 를 넘는다",
            MAX_UNARY);
      }
    }
    return (q << k) | (k > 0 ? r.readBits(k) : 0);
  }

  // 골든 코덱 (SPEC §2.6) — 바이트마다 gamma(b+1).
  public static byte[] encode(byte[] src) {
    BitIO.MsbWriter w = new BitIO.MsbWriter();
    for (byte b : src) {
      putGamma(w, (b & 0xFF) + 1);
    }
    w.flush();
    ByteBuf out = new ByteBuf();
    Varint.put(out, src.length);
    out.extend(w.bytes());
    return out.bytes();
  }

  public static byte[] decode(byte[] src) {
    int[] h = Varint.getLength(src, 0);
    BitIO.MsbReader r = new BitIO.MsbReader(src, h[1]);
    byte[] out = new byte[h[0]];
    for (int i = 0; i < out.length; i++) {
      long v = getGamma(r) - 1;
      if (v < 0 || v > 255) {
        throw CodecException.of("바이트 범위를 벗어난 값: %d", v);
      }
      out[i] = (byte) v;
    }
    return out;
  }
}
