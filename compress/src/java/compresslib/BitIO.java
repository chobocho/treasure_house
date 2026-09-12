package compresslib;

/**
 * 비트 writer/reader — SPEC §1.
 *
 * <p>우리 형식은 전부 MSB 먼저이고 DEFLATE 만 LSB 먼저다. 가장 자주
 * 갈라지는 자리는 flush 의 채움이다 — <b>채움은 0</b> 이고, 쌓인 비트가
 * 없으면 바이트를 내보내지 않는다.
 */
public final class BitIO {
  private BitIO() {}

  /** 비트를 하나씩 내주는 것. 허프만 복호기가 이 모양만 요구한다. */
  public interface BitSource {
    int readBit();
  }

  public static final class MsbWriter {
    private final ByteBuf out = new ByteBuf();
    private int buf;
    private int n;

    public void writeBit(int bit) {
      buf |= (bit & 1) << (7 - n);
      if (++n == 8) {
        out.push(buf);
        buf = 0;
        n = 0;
      }
    }

    public void writeBits(long v, int count) {
      for (int i = count - 1; i >= 0; i--) {
        writeBit((int) ((v >>> i) & 1));
      }
    }

    /**
     * MSB 스트림에서는 값도 부호도 같은 순서다. 이름만 LsbWriter 와
     * 맞춘다.
     */
    public void writeCode(long code, int count) {
      writeBits(code, count);
    }

    public int bitPos() {
      return out.size() * 8 + n;
    }

    public void flush() {
      if (n > 0) {
        out.push(buf);
        buf = 0;
        n = 0;
      }
    }

    public byte[] bytes() {
      return out.bytes();
    }
  }

  public static final class MsbReader implements BitSource {
    private final byte[] src;
    public int pos;
    private int buf;
    private int n;

    public MsbReader(byte[] src, int pos) {
      this.src = src;
      this.pos = pos;
    }

    @Override
    public int readBit() {
      if (n == 0) {
        if (pos >= src.length) {
          throw new CodecException("비트 스트림이 바닥났다");
        }
        buf = src[pos++] & 0xFF;
        n = 8;
      }
      n--;
      return (buf >>> n) & 1;
    }

    public long readBits(int count) {
      long v = 0;
      for (int i = 0; i < count; i++) {
        v = (v << 1) | readBit();
      }
      return v;
    }

    public void align() {
      n = 0;
    }
  }

  public static final class LsbWriter {
    private final ByteBuf out = new ByteBuf();
    private int buf;
    private int n;

    public void writeBit(int bit) {
      buf |= (bit & 1) << n;
      if (++n == 8) {
        out.push(buf);
        buf = 0;
        n = 0;
      }
    }

    public void writeBits(long v, int count) {
      for (int i = 0; i < count; i++) {
        writeBit((int) ((v >>> i) & 1));
      }
    }

    /**
     * 허프만 부호만 같은 LSB 스트림에 높은 비트부터 넣는다 (RFC 1951).
     */
    public void writeCode(long code, int count) {
      for (int i = count - 1; i >= 0; i--) {
        writeBit((int) ((code >>> i) & 1));
      }
    }

    public int bitPos() {
      return out.size() * 8 + n;
    }

    public void flush() {
      if (n > 0) {
        out.push(buf);
        buf = 0;
        n = 0;
      }
    }

    public void align() {
      flush();
    }

    public byte[] bytes() {
      return out.bytes();
    }
  }

  public static final class LsbReader implements BitSource {
    private final byte[] src;
    public int pos;
    private int buf;
    private int n;

    public LsbReader(byte[] src, int pos) {
      this.src = src;
      this.pos = pos;
    }

    @Override
    public int readBit() {
      if (n == 0) {
        if (pos >= src.length) {
          throw new CodecException("비트 스트림이 바닥났다");
        }
        buf = src[pos++] & 0xFF;
        n = 8;
      }
      int bit = buf & 1;
      buf >>>= 1;
      n--;
      return bit;
    }

    public long readBits(int count) {
      long v = 0;
      for (int i = 0; i < count; i++) {
        v |= ((long) readBit()) << i;
      }
      return v;
    }

    public void align() {
      n = 0;
    }
  }

  // 골든 코덱 (SPEC §1.4). 앞의 0비트 셋이 요점 — 모든 바이트를 바이트
  // 경계 밖으로 밀어내므로, 몰래 복사하는 구현은 다른 파일을 낸다.
  public static final int PAD_BITS = 3;

  public static byte[] encode(byte[] src) {
    MsbWriter w = new MsbWriter();
    w.writeBits(0, PAD_BITS);
    for (byte b : src) {
      w.writeBits(b & 0xFF, 8);
    }
    w.flush();
    ByteBuf out = new ByteBuf();
    Varint.put(out, src.length);
    out.extend(w.bytes());
    return out.bytes();
  }

  public static byte[] decode(byte[] src) {
    int[] h = Varint.getLength(src, 0);
    MsbReader r = new MsbReader(src, h[1]);
    r.readBits(PAD_BITS);
    byte[] out = new byte[h[0]];
    for (int i = 0; i < out.length; i++) {
      out[i] = (byte) r.readBits(8);
    }
    return out;
  }
}
