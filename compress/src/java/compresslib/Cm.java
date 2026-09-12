package compresslib;

import java.util.Arrays;

/**
 * 문맥 혼합 — SPEC §18.
 *
 * <p>여기까지의 코덱은 모델을 <b>하나</b> 골랐다. 문맥 혼합은 고르지
 * 않는다 — 여러 모델에게 한꺼번에 묻고 <b>의견을 섞으면서</b> 누구를
 * 믿을지 배운다.
 *
 * <p>섞는 자리가 요점이다. 확률을 그냥 평균 내면 0.01 과 0.99 가 0.5 가
 * 되어 두 모델의 확신이 사라진다. <b>로지스틱 영역</b> 에서 더한다.
 */
public final class Cm {
  public static final int TABLE_BITS = 20;
  public static final int TABLE_SIZE = 1 << TABLE_BITS;
  public static final int NUM_MODELS = 5;
  public static final int PROB_ONE = 4096;
  public static final int PROB_HALF = PROB_ONE / 2;
  /**
   * 셈이 쌓일수록 천천히 움직인다. 처음 보는 문맥은 빨리 배우고 오래 본
   * 문맥은 흔들리지 않아야 한다 — 고정 비율 하나로는 둘 다 못 한다.
   */
  public static final int[] COUNTER_RATES =
      {1, 1, 2, 2, 3, 3, 4, 4, 4, 5, 5, 5, 5, 5, 5, 5};
  public static final int COUNTER_LIMIT = 15;
  public static final int MIXER_SHIFT = 16;
  public static final int MIXER_INIT = 1 << 14;
  /**
   * 믹서 갱신의 시프트. lpaq 과 같은 16이다. 10 으로 두면 가중치가 한
   * 걸음에 5만씩 튀어 모델이 수렴하지 못한다.
   */
  public static final int MIXER_UPDATE_SHIFT = 16;
  public static final int MIXER_LEARN = 16;
  public static final int MIXER_CLAMP = 1 << 20;
  public static final int APM_RATE = 7;
  public static final int APM1_CONTEXTS = 256;
  public static final int APM2_CONTEXTS = 1 << 16;
  private static final int HASH_A = 0x9E3779B1;
  private static final int HASH_B = 0x85EBCA6B;

  private Cm() {}

  // SQUASH-TABLE-BEGIN — gen_tables.py 가 다섯을 대조한다 (§18.6)
  public static final int[] SQUASH_TABLE = {
      1, 2, 3, 6, 10, 16, 27, 45, 73, 120, 194, 310, 488, 747, 1101,
      1546, 2047, 2549, 2994, 3348, 3607, 3785, 3901, 3975, 4024,
      4050, 4068, 4079, 4085, 4089, 4092, 4093, 4094};
  // SQUASH-TABLE-END

  /** 로지스틱: -2047..2047 → 0..4095. 표 사이를 직선으로 잇는다. */
  public static int squash(int d) {
    if (d > 2047) {
      return 4095;
    }
    if (d < -2047) {
      return 0;
    }
    int w = d & 127;
    int i = (d >> 7) + 16;
    return ((SQUASH_TABLE[i] * (128 - w)
             + SQUASH_TABLE[i + 1] * w + 64) >> 7);
  }

  /** squash 의 역. 표를 뒤집어 만든다 — 따로 적을 값이 아니다. */
  private static final short[] STRETCH_TABLE = makeStretch();

  private static short[] makeStretch() {
    short[] table = new short[PROB_ONE];
    int pi = 0;
    for (int x = -2047; x <= 2047; x++) {
      int v = squash(x);
      for (int p = pi; p <= v; p++) {
        table[p] = (short) x;
      }
      pi = v + 1;
    }
    for (int p = pi; p < PROB_ONE; p++) {
      table[p] = 2047;
    }
    return table;
  }

  public static int stretch(int p) {
    return STRETCH_TABLE[p];
  }

  private static int hashCtx(int ctx, int c0) {
    int h = (ctx * HASH_A) ^ (c0 * HASH_B);
    return h >>> (32 - TABLE_BITS);
  }

  /** 적응 확률 지도 — 믹서의 답을 문맥에 맞춰 다시 고친다 (§18.5). */
  public static final class Apm {
    private final int[] t;
    private int index;

    public Apm(int contexts) {
      t = new int[contexts * 33];
      for (int i = 0; i < t.length; i++) {
        t[i] = squash(((i % 33) - 16) * 128) * 16;
      }
    }

    public int pp(int pr, int cx) {
      // 곱수는 32 다. 표가 33칸이라 0..4095 를 0..32 로 펴야 끝까지
      // 쓴다. lpaq1 의 23 이면 위쪽 아홉 칸이 죽어 확률이 잘린다.
      int s = (stretch(pr) + 2048) * 32;
      int wt = s & 0xFFF;
      int j = cx * 33 + (s >> 12);
      index = j + (wt >> 11);
      return (t[j] * (4096 - wt) + t[j + 1] * wt) >> 16;
    }

    public void update(int bit) {
      int g = (bit << 16) + (bit << APM_RATE) - bit - bit;
      t[index] += (g - t[index]) >> APM_RATE;
    }
  }

  /** 문맥 모델 다섯 + 믹서 + APM 둘. 부호기와 복호기가 똑같이 쓴다. */
  public static final class Model {
    private final char[] order0 = new char[256];
    private final byte[] order0n = new byte[256];
    private final char[][] tables = new char[4][];
    private final byte[][] counts = new byte[4][];
    private final int[] weights = new int[256 * NUM_MODELS];
    private final Apm apm1 = new Apm(APM1_CONTEXTS);
    private final Apm apm2 = new Apm(APM2_CONTEXTS);
    private int history;
    private int c0 = 1;
    private final int[] slots = new int[NUM_MODELS];
    private final int[] st = new int[NUM_MODELS];
    private int pMix = PROB_HALF;

    public Model() {
      Arrays.fill(order0, (char) PROB_HALF);
      for (int k = 0; k < 4; k++) {
        tables[k] = new char[TABLE_SIZE];
        Arrays.fill(tables[k], (char) PROB_HALF);
        counts[k] = new byte[TABLE_SIZE];
      }
      Arrays.fill(weights, MIXER_INIT);
    }

    public int predict() {
      int c0v = c0;
      int h = history;
      slots[0] = c0v & 0xFF;
      for (int k = 0; k < 4; k++) {
        int mask = k < 3 ? (1 << (8 * (k + 1))) - 1 : 0xFFFFFFFF;
        int ctx = h & mask;
        slots[k + 1] = hashCtx(ctx + (k + 1) * 0x01000193, c0v);
      }
      int[] probs = new int[NUM_MODELS];
      probs[0] = order0[slots[0]];
      for (int k = 0; k < 4; k++) {
        probs[k + 1] = tables[k][slots[k + 1]];
      }
      int wbase = (c0v & 0xFF) * NUM_MODELS;
      long dot = 0;
      for (int i = 0; i < NUM_MODELS; i++) {
        st[i] = stretch(probs[i]);
        dot += (long) weights[wbase + i] * st[i];
      }
      dot >>= MIXER_SHIFT;
      if (dot > 2047) {
        dot = 2047;
      }
      if (dot < -2047) {
        dot = -2047;
      }
      pMix = squash((int) dot);
      int p = (pMix + 3 * apm1.pp(pMix, c0v & 0xFF)) >> 2;
      int cx2 = ((c0v & 0xFF) << 8) | (h & 0xFF);
      p = (p + 3 * apm2.pp(p, cx2)) >> 2;
      if (p < 1) {
        p = 1;
      }
      if (p > 4094) {
        p = 4094;
      }
      return p;
    }

    public void update(int bit) {
      int target = bit << 12;
      int i0 = slots[0];
      order0[i0] = (char) (order0[i0]
          + ((target - order0[i0]) >> COUNTER_RATES[order0n[i0]]));
      if (order0n[i0] < COUNTER_LIMIT) {
        order0n[i0]++;
      }
      for (int k = 0; k < 4; k++) {
        int i = slots[k + 1];
        char[] t = tables[k];
        byte[] c = counts[k];
        t[i] = (char) (t[i] + ((target - t[i]) >> COUNTER_RATES[c[i]]));
        if (c[i] < COUNTER_LIMIT) {
          c[i]++;
        }
      }
      int err = (target - pMix) * MIXER_LEARN;
      int wbase = (c0 & 0xFF) * NUM_MODELS;
      for (int i = 0; i < NUM_MODELS; i++) {
        long v = weights[wbase + i] + (((long) st[i] * err)
            >> MIXER_UPDATE_SHIFT);
        if (v > MIXER_CLAMP) {
          v = MIXER_CLAMP;
        }
        if (v < -MIXER_CLAMP) {
          v = -MIXER_CLAMP;
        }
        weights[wbase + i] = (int) v;
      }
      apm1.update(bit);
      apm2.update(bit);
      c0 = (c0 << 1) | bit;
      if (c0 >= 256) {
        history = (history << 8) | (c0 & 0xFF);
        c0 = 1;
      }
    }
  }

  public static byte[] encode(byte[] src) {
    if (src.length == 0) {
      return Varint.put(0);
    }
    RangeCoder.Encoder enc = new RangeCoder.Encoder();
    Model model = new Model();
    for (byte raw : src) {
      int b = raw & 0xFF;
      for (int i = 7; i >= 0; i--) {
        int bit = (b >>> i) & 1;
        int p = model.predict();
        // 코더는 P(0) 을 받는다. 모델은 P(1) 을 내므로 뒤집는다.
        enc.encodeBitP0(PROB_ONE - p, bit);
        model.update(bit);
      }
    }
    enc.flush();
    ByteBuf out = new ByteBuf();
    Varint.put(out, src.length);
    out.extend(enc.bytes());
    return out.bytes();
  }

  public static byte[] decode(byte[] src) {
    int[] h = Varint.getLength(src, 0);
    int n = h[0];
    if (n == 0) {
      if (h[1] != src.length) {
        throw new CodecException("빈 입력인데 뒤에 바이트가 있다");
      }
      return new byte[0];
    }
    RangeCoder.Decoder dec = new RangeCoder.Decoder(src, h[1]);
    Model model = new Model();
    byte[] out = new byte[n];
    for (int k = 0; k < n; k++) {
      int b = 0;
      for (int i = 0; i < 8; i++) {
        int p = model.predict();
        int bit = dec.decodeBitP0(PROB_ONE - p);
        model.update(bit);
        b = (b << 1) | bit;
      }
      out[k] = (byte) b;
    }
    return out;
  }
}
