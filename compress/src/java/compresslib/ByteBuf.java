package compresslib;

import java.util.Arrays;

/**
 * 늘어나는 바이트 버퍼.
 *
 * <p>ByteArrayOutputStream 을 쓰지 않는 이유: 이미 쓴 바이트를 다시
 * 읽어야 하는 자리가 있다. LZ77 의 겹치는 일치(거리 1 짜리 긴 복사)는
 * 방금 쓴 바이트를 그 자리에서 다시 읽으며 한 바이트씩 나아간다.
 */
public final class ByteBuf {
  private byte[] buf = new byte[64];
  private int len;

  public void push(int b) {
    if (len == buf.length) {
      buf = Arrays.copyOf(buf, len * 2);
    }
    buf[len++] = (byte) b;
  }

  public void extend(byte[] src, int from, int to) {
    int need = len + (to - from);
    if (need > buf.length) {
      buf = Arrays.copyOf(buf, Math.max(need, len * 2));
    }
    System.arraycopy(src, from, buf, len, to - from);
    len = need;
  }

  public void extend(byte[] src) {
    extend(src, 0, src.length);
  }

  /**
   * i번째 바이트를 0..255 로. 자바의 byte 는 부호가 있다 (SPEC §0.5).
   */
  public int at(int i) {
    return buf[i] & 0xFF;
  }

  public int size() {
    return len;
  }

  public byte[] bytes() {
    return Arrays.copyOf(buf, len);
  }
}
