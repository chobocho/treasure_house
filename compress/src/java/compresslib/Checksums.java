package compresslib;

/**
 * Adler-32 과 CRC-32 — SPEC §10.8.
 *
 * <p>표는 다항식에서 만든다. 숫자 256개를 다섯 언어에 옮겨 적으면
 * 틀린다. 결과는 int 에 담되 부호 없는 값으로 본다 — 비교할 때 == 는
 * 안전하지만 출력할 때는 &amp; 0xFFFFFFFFL 로 올려야 한다.
 */
public final class Checksums {
  public static final int ADLER_MOD = 65521;
  /** b 가 32비트를 넘기 전에 나눠야 하는 폭 (zlib 의 NMAX) */
  public static final int ADLER_NMAX = 5552;
  public static final int CRC_POLY = 0xEDB88320;

  private Checksums() {}

  public static int adler32(byte[] data) {
    long a = 1;
    long b = 0;
    for (int i = 0; i < data.length; i += ADLER_NMAX) {
      int end = Math.min(data.length, i + ADLER_NMAX);
      for (int j = i; j < end; j++) {
        a += data[j] & 0xFF;
        b += a;
      }
      a %= ADLER_MOD;
      b %= ADLER_MOD;
    }
    return (int) ((b << 16) | a);
  }

  private static final int[] CRC_TABLE = makeCrcTable();

  private static int[] makeCrcTable() {
    int[] t = new int[256];
    for (int i = 0; i < 256; i++) {
      int c = i;
      for (int k = 0; k < 8; k++) {
        c = (c & 1) != 0 ? (c >>> 1) ^ CRC_POLY : c >>> 1;
      }
      t[i] = c;
    }
    return t;
  }

  public static int crc32(byte[] data) {
    int c = 0xFFFFFFFF;
    for (byte b : data) {
      c = CRC_TABLE[(c ^ b) & 0xFF] ^ (c >>> 8);
    }
    return c ^ 0xFFFFFFFF;
  }
}
