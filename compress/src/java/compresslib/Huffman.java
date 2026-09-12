package compresslib;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Comparator;
import java.util.List;

/**
 * 캐노니컬 허프만 — SPEC §5.
 *
 * <p>트리를 만들지 않는다. 최적 길이 벡터는 하나가 아니어서(1,1,1,1 은
 * 두 벌이 다 최적) 트리를 만들면 우선순위 큐의 동점 처리가 어느 쪽을
 * 고를지 정하는데, 그 처리는 언어마다 다르다. package–merge 의 정렬 키
 * (무게, 종류, 순번) 가 동점 처리 전부이고, 그 키 덕분에 결과가 빈도
 * 벡터만의 함수가 된다.
 */
public final class Huffman {
  public static final int MAX_LENGTH = 15;
  public static final int ALPHABET = 256;
  public static final int TABLE_BYTES = ALPHABET / 2;

  private Huffman() {}

  /**
   * 동전 하나. kind 0 이 기호, 1 이 꾸러미 — 무게가 같으면 기호가
   * 앞선다.
   */
  private static final class Coin {
    final long weight;
    final int kind;
    final int rank;
    final int[] syms;

    Coin(long weight, int kind, int rank, int[] syms) {
      this.weight = weight;
      this.kind = kind;
      this.rank = rank;
      this.syms = syms;
    }
  }

  private static final Comparator<Coin> COIN_ORDER =
      Comparator.<Coin>comparingLong(c -> c.weight)
          .thenComparingInt(c -> c.kind)
          .thenComparingInt(c -> c.rank);

  public static int[] codeLengths(long[] freqs, int limit) {
    List<int[]> used = new ArrayList<>();   // {빈도(int 로 충분), 기호}
    List<long[]> pairs = new ArrayList<>();
    for (int s = 0; s < freqs.length; s++) {
      if (freqs[s] > 0) {
        pairs.add(new long[] {freqs[s], s});
      }
    }
    pairs.sort((a, b) -> a[0] != b[0] ? Long.compare(a[0], b[0])
                                      : Long.compare(a[1], b[1]));
    for (long[] p : pairs) {
      used.add(new int[] {(int) p[1]});
    }
    int[] lengths = new int[freqs.length];
    int m = pairs.size();
    if (m == 0) {
      return lengths;
    }
    if (m == 1) {
      lengths[(int) pairs.get(0)[1]] = 1;
      return lengths;
    }
    if (limit < 31 && m > (1 << limit)) {
      throw CodecException.of("기호 %d개는 길이 %d 로 못 담는다",
          m, limit);
    }
    Coin[] coins = new Coin[m];
    for (int j = 0; j < m; j++) {
      coins[j] = new Coin(pairs.get(j)[0], 0, j, used.get(j));
    }
    List<Coin> level = new ArrayList<>(Arrays.asList(coins));
    for (int round = 0; round < limit - 1; round++) {
      List<Coin> packed = new ArrayList<>();
      for (int i = 0; i + 1 < level.size(); i += 2) {
        Coin a = level.get(i);
        Coin b = level.get(i + 1);
        int[] syms = new int[a.syms.length + b.syms.length];
        System.arraycopy(a.syms, 0, syms, 0, a.syms.length);
        System.arraycopy(b.syms, 0, syms, a.syms.length, b.syms.length);
        packed.add(
            new Coin(a.weight + b.weight, 1, packed.size(), syms));
      }
      level = packed;
      level.addAll(Arrays.asList(coins));
      level.sort(COIN_ORDER);
    }
    int take = Math.min(2 * m - 2, level.size());
    for (int i = 0; i < take; i++) {
      for (int s : level.get(i).syms) {
        lengths[s] += 1;
      }
    }
    return lengths;
  }

  public static int[] canonicalCodes(int[] lengths) {
    int[] blCount = new int[MAX_LENGTH + 1];
    for (int l : lengths) {
      if (l > 0) {
        if (l > MAX_LENGTH) {
          throw CodecException.of("부호 길이 %d 는 상한을 넘는다", l);
        }
        blCount[l]++;
      }
    }
    int[] nextCode = new int[MAX_LENGTH + 2];
    int code = 0;
    for (int bits = 1; bits <= MAX_LENGTH; bits++) {
      code = (code + blCount[bits - 1]) << 1;
      nextCode[bits] = code;
    }
    int[] codes = new int[lengths.length];
    for (int s = 0; s < lengths.length; s++) {
      int l = lengths[s];
      if (l == 0) {
        continue;
      }
      if (nextCode[l] >= (1 << l)) {
        throw CodecException.of("부호표가 넘친다 — 길이 %d", l);
      }
      codes[s] = nextCode[l]++;
    }
    return codes;
  }

  /**
   * 크래프트 합이 1 인지. 예외는 <b>기호 하나짜리 표</b> — 길이 1
   * 하나라 늘 합이 1/2 이고, zeros_64k 처럼 한 바이트만 있는 파일에서
   * 반드시 나온다.
   */
  public static void checkComplete(int[] lengths) {
    checkComplete(lengths, MAX_LENGTH);
  }

  /** bzip2 는 부호 길이가 20까지 간다 (§15.4). 기본은 15 그대로다. */
  public static void checkComplete(int[] lengths, int maxLength) {
    long total = 0;
    int used = 0;
    int only = 0;
    for (int l : lengths) {
      if (l > 0) {
        total += 1L << (maxLength - l);
        used++;
        only = l;
      }
    }
    long full = 1L << maxLength;
    if (total > full) {
      throw new CodecException("부호표가 넘친다 (크래프트 합 > 1)");
    }
    if (total < full && !(used == 1 && only == 1)) {
      throw new CodecException("부호표가 모자란다 (크래프트 합 < 1)");
    }
  }

  /**
   * 캐노니컬 복호기 — 트리를 안 만든다. 길이별 첫 부호와 첫 자리만
   * 있으면 비트를 하나씩 받아 가며 판정할 수 있다.
   */
  public static final class Decoder {
    private final int[] symbols;
    private final int[] count;
    private final int[] firstCode;
    private final int[] firstIndex;
    private final int maxLength;

    public Decoder(int[] lengths) {
      this(lengths, MAX_LENGTH);
    }

    public Decoder(int[] lengths, int maxLength) {
      this.maxLength = maxLength;
      count = new int[maxLength + 1];
      firstCode = new int[maxLength + 2];
      firstIndex = new int[maxLength + 2];
      List<int[]> pairs = new ArrayList<>();
      for (int s = 0; s < lengths.length; s++) {
        if (lengths[s] > 0) {
          pairs.add(new int[] {lengths[s], s});
        }
      }
      pairs.sort((a, b) -> a[0] != b[0] ? a[0] - b[0] : a[1] - b[1]);
      symbols = new int[pairs.size()];
      for (int i = 0; i < pairs.size(); i++) {
        symbols[i] = pairs.get(i)[1];
        count[pairs.get(i)[0]]++;
      }
      int code = 0;
      int index = 0;
      for (int l = 1; l <= maxLength; l++) {
        code = (code + count[l - 1]) << 1;
        firstCode[l] = code;
        firstIndex[l] = index;
        index += count[l];
      }
    }

    public int read(BitIO.BitSource r) {
      int code = 0;
      for (int l = 1; l <= maxLength; l++) {
        code = (code << 1) | r.readBit();
        int off = code - firstCode[l];
        if (count[l] > 0 && off < count[l]) {
          return symbols[firstIndex[l] + off];
        }
      }
      throw new CodecException("부호표에 없는 비트열");
    }
  }

  public static int nibble(byte[] table, int sym) {
    int b = table[sym >> 1] & 0xFF;
    return (sym & 1) == 1 ? (b & 0x0F) : (b >>> 4);
  }

  public static byte[] packTable(int[] lengths) {
    byte[] table = new byte[TABLE_BYTES];
    for (int s = 0; s < ALPHABET; s++) {
      int v = lengths[s] & 0x0F;
      if ((s & 1) == 1) {
        table[s >> 1] |= (byte) v;
      } else {
        table[s >> 1] |= (byte) (v << 4);
      }
    }
    return table;
  }

  public static byte[] encode(byte[] src) {
    if (src.length == 0) {
      return Varint.put(0);
    }
    long[] freqs = new long[ALPHABET];
    for (byte b : src) {
      freqs[b & 0xFF]++;
    }
    int[] lengths = codeLengths(freqs, MAX_LENGTH);
    int[] codes = canonicalCodes(lengths);
    BitIO.MsbWriter w = new BitIO.MsbWriter();
    for (byte b : src) {
      int s = b & 0xFF;
      w.writeBits(codes[s], lengths[s]);
    }
    w.flush();
    ByteBuf out = new ByteBuf();
    Varint.put(out, src.length);
    out.extend(packTable(lengths));
    out.extend(w.bytes());
    return out.bytes();
  }

  public static byte[] decode(byte[] src) {
    int[] h = Varint.getLength(src, 0);
    int n = h[0];
    int pos = h[1];
    if (n == 0) {
      if (pos != src.length) {
        throw new CodecException("빈 입력인데 뒤에 바이트가 있다");
      }
      return new byte[0];
    }
    if (src.length < pos + TABLE_BYTES) {
      throw new CodecException("부호 길이 표가 잘렸다");
    }
    byte[] table = Arrays.copyOfRange(src, pos, pos + TABLE_BYTES);
    int[] lengths = new int[ALPHABET];
    for (int s = 0; s < ALPHABET; s++) {
      lengths[s] = nibble(table, s);
    }
    checkComplete(lengths);
    Decoder dec = new Decoder(lengths);
    BitIO.MsbReader r = new BitIO.MsbReader(src, pos + TABLE_BYTES);
    byte[] out = new byte[n];
    for (int i = 0; i < n; i++) {
      out[i] = (byte) dec.read(r);
    }
    return out;
  }
}
