package compresslib;

/**
 * LEB128 가변 길이 정수 — SPEC §2.1.
 *
 * <p>명세에서는 IntCode 의 일부지만 클래스를 갈랐다. 모든 코덱 헤더가
 * varint 로 시작하는데 IntCode 는 비트 스트림을 쓰고 BitIO 의 골든
 * 코덱은 다시 varint 를 쓴다. 다섯 언어 모두 같은 이유로 같게 갈라
 * 뒀다.
 */
public final class Varint {
  public static final int MAX_BYTES = 10;
  /**
   * 길이 칸의 상한. 손상된 헤더가 불가능한 할당을 요구하지 못하게
   * 막는다.
   */
  public static final long MAX_LENGTH = 0xFFFFFFFFL;

  private Varint() {}

  public static void put(ByteBuf out, long value) {
    for (;;) {
      int b = (int) (value & 0x7F);
      value >>>= 7;
      if (value != 0) {
        out.push(b | 0x80);
      } else {
        out.push(b);
        return;
      }
    }
  }

  public static byte[] put(long value) {
    ByteBuf out = new ByteBuf();
    put(out, value);
    return out.bytes();
  }

  /**
   * 읽은 값과 다음 위치를 함께 돌려준다. 자바에는 튜플이 없어 배열로
   * 담는다.
   */
  public static long[] get(byte[] src, int pos) {
    long value = 0;
    int shift = 0;
    for (int i = 0; i < MAX_BYTES; i++) {
      if (pos >= src.length) {
        throw new CodecException("varint 가 잘렸다");
      }
      int b = src[pos++] & 0xFF;
      if (i == MAX_BYTES - 1 && (b & 0x7F) > 1) {
        throw new CodecException("varint 가 64비트를 넘는다");
      }
      value |= (long) (b & 0x7F) << shift;
      if ((b & 0x80) == 0) {
        return new long[] {value, pos};
      }
      shift += 7;
    }
    throw CodecException.of("varint 가 %d바이트를 넘는다", MAX_BYTES);
  }

  public static int[] getLength(byte[] src, int pos) {
    long[] r = get(src, pos);
    if (r[0] > MAX_LENGTH) {
      throw CodecException.of("길이 칸이 너무 크다: %d", r[0]);
    }
    return new int[] {(int) r[0], (int) r[1]};
  }
}
