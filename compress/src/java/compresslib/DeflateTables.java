package compresslib;

/**
 * DEFLATE 의 표들 — SPEC §10.3 (RFC 1951).
 *
 * <p>길이 부호 284 는 227..257 까지만 적을 수 있고, <b>길이 258 은 늘
 * 285</b> 다. 284 + 여분 31 로도 258 이 되지만 진짜 부호기는 아무도
 * 그러지 않는다.
 */
public final class DeflateTables {
  public static final int MIN_MATCH = 3;
  public static final int MAX_MATCH = 258;
  public static final int MAX_DIST = 32768;
  public static final int END_OF_BLOCK = 256;
  public static final int LITLEN_SYMBOLS = 286;
  public static final int DIST_SYMBOLS = 30;
  public static final int CL_SYMBOLS = 19;
  public static final int CL_MAX_LENGTH = 7;
  public static final int CL_REPEAT = 16;
  public static final int CL_ZERO_SHORT = 17;
  public static final int CL_ZERO_LONG = 18;

  private DeflateTables() {}

  public static final int[] LENGTH_EXTRA = {
      0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2,
      2, 3, 3, 3, 3, 4, 4, 4, 4, 5, 5, 5, 5, 0};
  public static final int[] LENGTH_BASE = {
      3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 15, 17, 19, 23,
      27, 31, 35, 43, 51, 59, 67, 83, 99, 115, 131, 163, 195, 227, 258};
  public static final int[] DIST_EXTRA = {
      0, 0, 0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6,
      6, 7, 7, 8, 8, 9, 9, 10, 10, 11, 11, 12, 12, 13, 13};
  public static final int[] DIST_BASE = {
      1, 2, 3, 4, 5, 7, 9, 13, 17, 25,
      33, 49, 65, 97, 129, 193, 257, 385, 513, 769,
      1025, 1537, 2049, 3073, 4097, 6145, 8193, 12289, 16385, 24577};

  /**
   * 자주 0 이 되는 것을 뒤로 몰아 HCLEN 으로 꼬리를 자를 수 있게 한
   * 순서.
   */
  public static final int[] CL_ORDER = {
      16, 17, 18, 0, 8, 7, 9, 6, 10, 5, 11, 4, 12, 3, 13, 2, 14, 1, 15};

  public static final int[] LENGTH_CODE = makeLengthCode();

  private static int[] makeLengthCode() {
    int[] t = new int[MAX_MATCH + 1];
    for (int code = 0; code < LENGTH_BASE.length; code++) {
      int base = LENGTH_BASE[code];
      int top = base + (1 << LENGTH_EXTRA[code]) - 1;
      if (base == MAX_MATCH) {
        top = MAX_MATCH;
      }
      for (int ln = base; ln <= top && ln <= MAX_MATCH; ln++) {
        t[ln] = 257 + code;
      }
    }
    t[MAX_MATCH] = 285;   // 284 가 아니라 285 로 못 박는다
    return t;
  }

  public static int distCode(int dist) {
    for (int code = DIST_SYMBOLS - 1; code >= 0; code--) {
      if (dist >= DIST_BASE[code]) {
        return code;
      }
    }
    throw CodecException.of("거리가 1보다 작다: %d", dist);
  }

  public static final int[] FIXED_LITLEN = makeFixedLitlen();
  public static final int[] FIXED_DIST = makeFixedDist();

  private static int[] makeFixedLitlen() {
    int[] l = new int[288];
    for (int s = 0; s < 288; s++) {
      if (s < 144) {
        l[s] = 8;
      } else if (s < 256) {
        l[s] = 9;
      } else if (s < 280) {
        l[s] = 7;
      } else {
        l[s] = 8;
      }
    }
    return l;
  }

  private static int[] makeFixedDist() {
    int[] l = new int[32];
    java.util.Arrays.fill(l, 5);
    return l;
  }
}
