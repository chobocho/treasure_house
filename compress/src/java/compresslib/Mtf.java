package compresslib;

/**
 * move-to-front — SPEC §4.
 *
 * <p>앞으로 <b>옮기는</b> 것이지 바꿔치는 것이 아니다. 바꿔치기도
 * 자기들끼리는 왕복이 되므로, 골든 벡터가 없으면 갈라진 줄도 모른다.
 */
public final class Mtf {
  public static final int ALPHABET = 256;

  private Mtf() {}

  private static byte[] identity() {
    byte[] t = new byte[ALPHABET];
    for (int i = 0; i < ALPHABET; i++) {
      t[i] = (byte) i;
    }
    return t;
  }

  public static byte[] transform(byte[] src) {
    byte[] table = identity();
    byte[] out = new byte[src.length];
    for (int p = 0; p < src.length; p++) {
      byte b = src[p];
      int i = 0;
      while (table[i] != b) {
        i++;
      }
      out[p] = (byte) i;
      for (int k = i; k > 0; k--) {
        table[k] = table[k - 1];
      }
      table[0] = b;
    }
    return out;
  }

  public static byte[] inverse(byte[] src) {
    byte[] table = identity();
    byte[] out = new byte[src.length];
    for (int p = 0; p < src.length; p++) {
      int idx = src[p] & 0xFF;
      byte b = table[idx];
      out[p] = b;
      for (int k = idx; k > 0; k--) {
        table[k] = table[k - 1];
      }
      table[0] = b;
    }
    return out;
  }

  public static byte[] encode(byte[] src) {
    ByteBuf out = new ByteBuf();
    Varint.put(out, src.length);
    out.extend(transform(src));
    return out.bytes();
  }

  public static byte[] decode(byte[] src) {
    int[] h = Varint.getLength(src, 0);
    if (src.length - h[1] != h[0]) {
      throw CodecException.of("몸통 길이가 헤더와 다르다: %d != %d",
          src.length - h[1], h[0]);
    }
    byte[] body = java.util.Arrays.copyOfRange(src, h[1], src.length);
    return inverse(body);
  }
}
