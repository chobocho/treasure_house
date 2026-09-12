package compresslib;

import java.util.Arrays;

/**
 * LZMA1 복호기 — SPEC §16.
 *
 * <p>§8 의 레인지 코더를 LZMA 것으로 쓴 이유가 이 파일이다. 같은 코더에
 * LZMA 의 문맥 모델만 얹으면 진짜 xz 가 만든 파일이 풀린다.
 *
 * <p>읽는 것은 LZMA1 "alone" 형식이다. .xz 컨테이너는 다른 틀이고
 * 12부에서 말로만 다룬다 — "LZMA 를 푼다" 와 ".xz 를 푼다" 는 다른
 * 주장이다.
 */
public final class LzmaDec {
  public static final int NUM_STATES = 12;
  public static final int NUM_POS_BITS_MAX = 4;
  public static final int NUM_LEN_TO_POS_STATES = 4;
  public static final int NUM_ALIGN_BITS = 4;
  public static final int END_POS_MODEL_INDEX = 14;
  public static final int NUM_FULL_DISTANCES =
      1 << (END_POS_MODEL_INDEX >> 1);
  public static final int MATCH_MIN_LEN = 2;
  public static final long UNKNOWN_SIZE = -1L;      // 0xFFFF...FFFF
  public static final long END_MARKER = 0xFFFFFFFFL;
  public static final long MAX_OUTPUT = 1L << 32;

  private LzmaDec() {}

  private static int[] probs(int n) {
    int[] p = new int[n];
    Arrays.fill(p, RangeCoder.PROB_INIT);
    return p;
  }

  /** 위에서부터 내려가는 이진 트리. 결과는 numBits 짜리 값. */
  private static int bitTree(RangeCoder.Decoder dec, int[] p,
      int offset, int numBits) {
    int m = 1;
    for (int i = 0; i < numBits; i++) {
      m = (m << 1) + dec.decodeBit(p, offset + m);
    }
    return m - (1 << numBits);
  }

  /** 같은 트리인데 비트를 <b>거꾸로</b> 모은다 — 거리의 아래쪽이다. */
  private static int bitTreeReverse(RangeCoder.Decoder dec, int[] p,
      int offset, int numBits) {
    int m = 1;
    int sym = 0;
    for (int i = 0; i < numBits; i++) {
      int bit = dec.decodeBit(p, offset + m);
      m = (m << 1) + bit;
      sym |= bit << i;
    }
    return sym;
  }

  /** 길이 복호기. 2..273 을 세 구간(8+8+256)으로 나눠 적는다. */
  private static final class LengthCoder {
    final int[] choice = probs(2);
    final int[] low;
    final int[] mid;
    final int[] high = probs(256);

    LengthCoder(int posStates) {
      low = probs(posStates * 8);
      mid = probs(posStates * 8);
    }

    int decode(RangeCoder.Decoder dec, int posState) {
      if (dec.decodeBit(choice, 0) == 0) {
        return bitTree(dec, low, posState * 8, 3);
      }
      if (dec.decodeBit(choice, 1) == 0) {
        return 8 + bitTree(dec, mid, posState * 8, 3);
      }
      return 16 + bitTree(dec, high, 0, 8);
    }
  }

  /** 머리에서 읽은 값들. 자바에는 튜플이 없어 작은 클래스로 담는다. */
  public static final class Header {
    public final int lc;
    public final int lp;
    public final int pb;
    public final long dictSize;
    public final long size;
    public final int pos;

    Header(int lc, int lp, int pb, long dictSize, long size, int pos) {
      this.lc = lc;
      this.lp = lp;
      this.pb = pb;
      this.dictSize = dictSize;
      this.size = size;
      this.pos = pos;
    }
  }

  public static Header parseHeader(byte[] src) {
    if (src.length < 13) {
      throw new CodecException("LZMA 머리가 너무 짧다");
    }
    int prop = src[0] & 0xFF;
    if (prop >= 9 * 5 * 5) {
      throw CodecException.of("속성 바이트가 범위를 넘는다: %d", prop);
    }
    int lc = prop % 9;
    int rest = prop / 9;
    int lp = rest % 5;
    int pb = rest / 5;
    long dictSize = 0;
    for (int i = 0; i < 4; i++) {
      dictSize |= (src[1 + i] & 0xFFL) << (8 * i);
    }
    long size = 0;
    for (int i = 0; i < 8; i++) {
      size |= (src[5 + i] & 0xFFL) << (8 * i);
    }
    if (size != UNKNOWN_SIZE && (size < 0 || size > MAX_OUTPUT)) {
      throw new CodecException("원본 길이가 너무 크다");
    }
    return new Header(lc, lp, pb, dictSize, size, 13);
  }

  public static byte[] decode(byte[] src) {
    Header h = parseHeader(src);
    RangeCoder.Decoder dec = new RangeCoder.Decoder(src, h.pos);
    int posStates = 1 << h.pb;
    int posMask = posStates - 1;
    int lpMask = (1 << h.lp) - 1;

    int[] isMatch = probs(NUM_STATES << NUM_POS_BITS_MAX);
    int[] isRep = probs(NUM_STATES);
    int[] isRepG0 = probs(NUM_STATES);
    int[] isRepG1 = probs(NUM_STATES);
    int[] isRepG2 = probs(NUM_STATES);
    int[] isRep0Long = probs(NUM_STATES << NUM_POS_BITS_MAX);
    int[] posSlot = probs(NUM_LEN_TO_POS_STATES * 64);
    int[] specPos = probs(NUM_FULL_DISTANCES - END_POS_MODEL_INDEX + 1);
    int[] alignProbs = probs(1 << NUM_ALIGN_BITS);
    int[] literal = probs(0x300 << (h.lc + h.lp));
    LengthCoder lenCoder = new LengthCoder(posStates);
    LengthCoder repLenCoder = new LengthCoder(posStates);

    ByteBuf out = new ByteBuf();
    int state = 0;
    int rep0 = 0;
    int rep1 = 0;
    int rep2 = 0;
    int rep3 = 0;

    while (h.size == UNKNOWN_SIZE || out.size() < h.size) {
      int posState = out.size() & posMask;
      int midx = (state << NUM_POS_BITS_MAX) + posState;
      int length;
      if (dec.decodeBit(isMatch, midx) == 0) {
        int prev = out.size() > 0 ? out.at(out.size() - 1) : 0;
        int litState = ((out.size() & lpMask) << h.lc)
            + (prev >>> (8 - h.lc));
        int base = 0x300 * litState;
        int symbol = 1;
        if (state >= 7) {
          // 일치 뒤의 리터럴 — 앞 일치의 같은 자리 바이트에 견준다
          if (rep0 + 1 > out.size()) {
            throw new CodecException("거리가 지금까지 낸 것보다 멀다");
          }
          int matchByte = out.at(out.size() - rep0 - 1);
          while (symbol < 0x100) {
            int matchBit = (matchByte >>> 7) & 1;
            matchByte = (matchByte << 1) & 0xFF;
            int bit = dec.decodeBit(literal,
                base + ((1 + matchBit) << 8) + symbol);
            symbol = (symbol << 1) | bit;
            if (matchBit != bit) {
              break;
            }
          }
        }
        while (symbol < 0x100) {
          symbol =
              (symbol << 1) | dec.decodeBit(literal, base + symbol);
        }
        out.push(symbol & 0xFF);
        state = state < 4 ? 0 : (state < 10 ? state - 3 : state - 6);
        continue;
      }

      if (dec.decodeBit(isRep, state) != 0) {
        // 지난 거리 넷 가운데 하나를 다시 쓴다 (§16.4)
        if (out.size() == 0) {
          throw new CodecException("첫 기호가 되풀이 일치다");
        }
        if (dec.decodeBit(isRepG0, state) == 0) {
          if (dec.decodeBit(isRep0Long, midx) == 0) {
            state = state < 7 ? 9 : 11;
            if (rep0 + 1 > out.size()) {
              throw new CodecException("거리가 낸 것보다 멀다");
            }
            out.push(out.at(out.size() - rep0 - 1));
            continue;
          }
        } else {
          int dist;
          if (dec.decodeBit(isRepG1, state) == 0) {
            dist = rep1;
          } else {
            if (dec.decodeBit(isRepG2, state) == 0) {
              dist = rep2;
            } else {
              dist = rep3;
              rep3 = rep2;
            }
            rep2 = rep1;
          }
          rep1 = rep0;
          rep0 = dist;
        }
        length = repLenCoder.decode(dec, posState) + MATCH_MIN_LEN;
        state = state < 7 ? 8 : 11;
      } else {
        rep3 = rep2;
        rep2 = rep1;
        rep1 = rep0;
        length = lenCoder.decode(dec, posState) + MATCH_MIN_LEN;
        state = state < 7 ? 7 : 10;
        int slotState = Math.min(length - MATCH_MIN_LEN,
            NUM_LEN_TO_POS_STATES - 1);
        int slot = bitTree(dec, posSlot, slotState * 64, 6);
        if (slot < 4) {
          rep0 = slot;
        } else {
          int direct = (slot >> 1) - 1;
          rep0 = (2 | (slot & 1)) << direct;
          if (slot < END_POS_MODEL_INDEX) {
            rep0 += bitTreeReverse(dec, specPos, rep0 - slot, direct);
          } else {
            rep0 += dec.decodeDirectBits(direct - NUM_ALIGN_BITS)
                << NUM_ALIGN_BITS;
            rep0 += bitTreeReverse(dec, alignProbs, 0, NUM_ALIGN_BITS);
          }
          if ((rep0 & 0xFFFFFFFFL) == END_MARKER) {
            break;
          }
        }
      }

      // 거리 검사는 한 곳에서만 한다 — 새 일치든 되풀이 일치든 같다.
      if (rep0 < 0 || rep0 >= out.size()) {
        throw new CodecException("거리가 지금까지 낸 것보다 멀다");
      }
      int start = out.size() - rep0 - 1;
      // 한 바이트씩 앞으로. 거리 1 짜리 긴 일치가 여기 기댄다.
      for (int j = 0; j < length; j++) {
        out.push(out.at(start + j));
      }
      if (out.size() > MAX_OUTPUT) {
        throw new CodecException("푼 길이가 상한을 넘는다");
      }
    }

    if (h.size != UNKNOWN_SIZE && out.size() != h.size) {
      throw CodecException.of("푼 길이가 머리와 다르다: %d != %d",
          out.size(), h.size);
    }
    return out.bytes();
  }
}
