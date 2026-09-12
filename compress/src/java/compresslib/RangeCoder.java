package compresslib;

/**
 * 이진 레인지 코더 — SPEC §8. LZMA 의 것 그대로.
 *
 * <p>자바에는 부호 없는 정수가 없다 (SPEC §0.5). range·code 는 int 에
 * 담되 <b>부호 없는 값으로 다룬다</b> — 크기 비교는
 * Integer.compareUnsigned, 오른쪽 시프트는 &gt;&gt;&gt;. (range
 * &gt;&gt;&gt; 11) * prob 은 int 로 계산하면 넘칠 수 있어 long 으로
 * 올려 곱한 뒤 되돌린다. low 는 2^33 까지 가므로 long 이다.
 */
public final class RangeCoder {
  public static final int PROB_BITS = 11;
  public static final int PROB_TOTAL = 1 << PROB_BITS;
  public static final int PROB_INIT = PROB_TOTAL / 2;
  public static final int MOVE_BITS = 5;
  public static final long TOP = 1L << 24;
  private static final long U32 = 0xFFFFFFFFL;

  private RangeCoder() {}

  public static final class Encoder {
    private long low;                 // 최대 2^33 — int 가 아니다
    private long range = U32;
    private int cache;
    private long cacheSize = 1;
    private final ByteBuf out = new ByteBuf();

    /** 위 바이트 하나를 확정해 내보낸다. 캐리는 앞으로 전파한다. */
    private void shiftLow() {
      if ((low >>> 32) != 0 || low < 0xFF000000L) {
        int carry = (int) (low >>> 32);
        int temp = cache;
        do {
          out.push((temp + carry) & 0xFF);
          temp = 0xFF;
          cacheSize--;
        } while (cacheSize != 0);
        cache = (int) ((low >>> 24) & 0xFF);
      }
      cacheSize++;
      low = (low << 8) & U32;
    }

    public void encodeBit(int[] probs, int i, int bit) {
      long bound = (range >>> PROB_BITS) * probs[i];
      if (bit == 0) {
        range = bound;
        probs[i] += (PROB_TOTAL - probs[i]) >>> MOVE_BITS;
      } else {
        low += bound;
        range -= bound;
        probs[i] -= probs[i] >>> MOVE_BITS;
      }
      while (range < TOP) {
        range = (range << 8) & U32;
        shiftLow();
      }
    }

    public void flush() {
      for (int i = 0; i < 5; i++) {
        shiftLow();
      }
    }

    public byte[] bytes() {
      return out.bytes();
    }
  }

  public static final class Decoder {
    private final byte[] src;
    private int pos;
    private long range = U32;
    private long code;

    public Decoder(byte[] src, int pos) {
      this.src = src;
      this.pos = pos;
      if (pos >= src.length) {
        throw new CodecException("레인지 코더 스트림이 비었다");
      }
      if (src[pos] != 0) {
        throw CodecException.of("첫 바이트가 0 이 아니다: %d",
            src[pos] & 0xFF);
      }
      this.pos++;
      for (int i = 0; i < 4; i++) {
        code = ((code << 8) | nextByte()) & U32;
      }
    }

    private int nextByte() {
      // 잘 만들어진 스트림도 마지막 판정에서 한 바이트쯤 더 읽는다.
      if (pos < src.length) {
        return src[pos++] & 0xFF;
      }
      pos++;
      if (pos > src.length + 5) {
        throw new CodecException("스트림 끝을 너무 많이 넘었다");
      }
      return 0;
    }

    public int decodeBit(int[] probs, int i) {
      long bound = (range >>> PROB_BITS) * probs[i];
      int bit;
      if (code < bound) {
        range = bound;
        probs[i] += (PROB_TOTAL - probs[i]) >>> MOVE_BITS;
        bit = 0;
      } else {
        code -= bound;
        range -= bound;
        probs[i] -= probs[i] >>> MOVE_BITS;
        bit = 1;
      }
      while (range < TOP) {
        range = (range << 8) & U32;
        code = ((code << 8) | nextByte()) & U32;
      }
      return bit;
    }
  }

  /**
   * 0차 적응 바이트 모델. 문맥은 1 에서 시작해 여덟 번 만에 256..511 이
   * 되므로 실제로 쓰이는 자리는 1..255 뿐 — 배열이 257 이 아니라 256
   * 이다.
   */
  public static final class ByteModel {
    final int[] probs = new int[256];

    public ByteModel() {
      java.util.Arrays.fill(probs, PROB_INIT);
    }

    public void encode(Encoder enc, int b) {
      int ctx = 1;
      for (int i = 7; i >= 0; i--) {
        int bit = (b >>> i) & 1;
        enc.encodeBit(probs, ctx, bit);
        ctx = (ctx << 1) | bit;
      }
    }

    public int decode(Decoder dec) {
      int ctx = 1;
      for (int i = 0; i < 8; i++) {
        ctx = (ctx << 1) | dec.decodeBit(probs, ctx);
      }
      return ctx - 256;
    }
  }

  public static byte[] encode(byte[] src) {
    if (src.length == 0) {
      return Varint.put(0);
    }
    Encoder enc = new Encoder();
    ByteModel m = new ByteModel();
    for (byte b : src) {
      m.encode(enc, b & 0xFF);
    }
    enc.flush();
    ByteBuf out = new ByteBuf();
    Varint.put(out, src.length);
    out.extend(enc.bytes());
    return out.bytes();
  }

  public static byte[] decode(byte[] src) {
    int[] h = Varint.getLength(src, 0);
    if (h[0] == 0) {
      if (h[1] != src.length) {
        throw new CodecException("빈 입력인데 뒤에 바이트가 있다");
      }
      return new byte[0];
    }
    Decoder dec = new Decoder(src, h[1]);
    ByteModel m = new ByteModel();
    byte[] out = new byte[h[0]];
    for (int i = 0; i < out.length; i++) {
      out[i] = (byte) m.decode(dec);
    }
    return out;
  }
}
