package compresslib;

import java.util.List;
import java.util.function.UnaryOperator;

/**
 * 알고리즘 이름 → 부호기·복호기. 이름이 곧 golden/ 의 디렉터리다.
 * 다섯 언어가 같은 이름·같은 순서를 갖는다.
 */
public final class Registry {
  private Registry() {}

  /** 한 알고리즘. encode·decode 는 byte[] → byte[] 하나짜리 함수다. */
  public static final class Entry {
    public final String name;
    /** 복호기만 있는 모듈에서는 null 이다 (PLAN.md §0.4). */
    public final UnaryOperator<byte[]> encode;
    public final UnaryOperator<byte[]> decode;

    Entry(String name, UnaryOperator<byte[]> encode,
        UnaryOperator<byte[]> decode) {
      this.name = name;
      this.encode = encode;
      this.decode = decode;
    }
  }

  /** 순서가 곧 배우는 순서다 (PLAN.md §3 Tier 1). */
  public static final List<Entry> ENTRIES = List.of(
      new Entry("bitio", BitIO::encode, BitIO::decode),
      new Entry("intcode", IntCode::encode, IntCode::decode),
      new Entry("rle", Rle::encode, Rle::decode),
      new Entry("mtf", Mtf::encode, Mtf::decode),
      new Entry("huffman", Huffman::encode, Huffman::decode),
      new Entry("lzss", Lzss::encode, Lzss::decode),
      new Entry("lzw", Lzw::encode, Lzw::decode),
      new Entry("rangecoder", RangeCoder::encode, RangeCoder::decode),
      new Entry("bwt", Bwt::encode, Bwt::decode),
      new Entry("deflate", Deflate::encode, Deflate::decode),
      new Entry("ans", Ans::encode, Ans::decode),
      new Entry("lz4block", Lz4Block::encode, Lz4Block::decode),
      new Entry("ppm", Ppm::encode, Ppm::decode),
      new Entry("cm", Cm::encode, Cm::decode),
      new Entry("lossy", Lossy::encode, Lossy::decode),
      // 복호기만 있는 모듈 (PLAN.md §0.4)
      new Entry("bzip2dec", null, Bzip2Dec::decode),
      new Entry("lzmadec", null, LzmaDec::decode));

  public static Entry find(String name) {
    for (Entry e : ENTRIES) {
      if (e.name.equals(name)) {
        return e;
      }
    }
    return null;
  }
}
