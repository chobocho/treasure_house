package compresslib;

import java.util.Arrays;

/**
 * 자바 시험 — JUnit 없이 main 하나로 돈다.
 *
 * <p>바깥 라이브러리를 안 쓰는 이유는 두 가지다. Maven·Gradle 이 없고,
 * 무엇보다 이 기계는 JVM 을 한 번에 하나만 띄울 수 있어서 시험 러너가
 * 프로세스를 더 띄우면 세션째 위험하다.
 *
 * <p>파이썬 쪽보다 얇다. 진짜 문지기는 파서티 검사(골든 대조 + 5×5 교차
 * 복호)이고, 여기서는 그 검사가 못 보는 것만 본다 — 예외를 던져야 할
 * 자리에서 진짜 던지는가, 그리고 명세의 표가 이 언어에서도 그대로
 * 나오는가.
 */
public final class RunTests {
  private static int checks;
  private static int failures;

  private RunTests() {}

  private static void check(boolean ok, String what) {
    checks++;
    if (!ok) {
      failures++;
      System.out.println("실패 " + what);
    }
  }

  private static void eq(byte[] got, byte[] want, String what) {
    check(Arrays.equals(got, want),
        what + " — " + Arrays.toString(got) + " != "
            + Arrays.toString(want));
  }

  private static byte[] b(int... v) {
    byte[] out = new byte[v.length];
    for (int i = 0; i < v.length; i++) {
      out[i] = (byte) v[i];
    }
    return out;
  }

  private static byte[] s(String text) {
    byte[] out = new byte[text.length()];
    for (int i = 0; i < text.length(); i++) {
      out[i] = (byte) text.charAt(i);
    }
    return out;
  }

  private static byte[] repeat(int value, int n) {
    byte[] out = new byte[n];
    Arrays.fill(out, (byte) value);
    return out;
  }

  private static byte[] pseudo(int n, int a, int c) {
    byte[] out = new byte[n];
    for (int i = 0; i < n; i++) {
      out[i] = (byte) ((i * a + c) & 0xFF);
    }
    return out;
  }

  private static boolean throwsCodec(Runnable r) {
    try {
      r.run();
    } catch (CodecException e) {
      return true;
    }
    return false;
  }

  private static void testBitio() {
    BitIO.MsbWriter w = new BitIO.MsbWriter();
    w.writeBit(1);
    w.flush();
    eq(w.bytes(), b(0x80), "첫 비트는 7번 비트에");

    BitIO.MsbWriter w2 = new BitIO.MsbWriter();
    w2.writeBits(0b111, 3);
    w2.flush();
    eq(w2.bytes(), b(0xE0), "채움은 0 이다");

    BitIO.LsbWriter w3 = new BitIO.LsbWriter();   // 빈 DEFLATE 스트림
    w3.writeBits(1, 1);
    w3.writeBits(1, 2);
    w3.writeCode(0, 7);
    w3.flush();
    eq(w3.bytes(), b(0x03, 0x00), "빈 DEFLATE");

    eq(BitIO.encode(new byte[0]), b(0x00, 0x00), "bitio 빈 입력");
  }

  private static void testIntcode() {
    eq(Varint.put(300), b(0xAC, 0x02), "varint(300)");
    long[] cases = {Long.MIN_VALUE, Long.MAX_VALUE, 0, -1, 1};
    for (long n : cases) {
      check(IntCode.unzigzag(IntCode.zigzag(n)) == n,
          "zigzag 왕복 " + n);
    }
    BitIO.MsbWriter w = new BitIO.MsbWriter();
    IntCode.putGamma(w, 4);                       // 00100
    w.flush();
    eq(w.bytes(), b(0x20), "gamma(4)");
    check(throwsCodec(() -> {
      BitIO.MsbWriter x = new BitIO.MsbWriter();
      IntCode.putRice(x, 1L << 40, 0);
    }), "rice 의 몫 상한");
  }

  private static void testRle() {
    eq(Rle.encode(s("AAA")), b(0x03, 0xFE, 'A'), "런 3");
    eq(Rle.encode(s("AB")), b(0x02, 0x01, 'A', 'B'), "리터럴 둘");
    eq(Rle.encode(repeat('A', 128)), b(0x80, 0x01, 0x81, 'A'),
        "런 상한 128");
    check(throwsCodec(() -> Rle.decode(b(0x03, 0x80, 'A', 'A', 'A'))),
        "제어 128 거절");
    check(Arrays.equals(Rle.zeroRunEncode(new int[] {0, 0, 0}),
        new int[] {0, 0}), "0런 3 = RUNA,RUNA");
  }

  private static void testMtf() {
    eq(Mtf.transform(s("AAAA")), b('A', 0, 0, 0), "되풀이");
    // 옮기는 것이지 바꿔치는 것이 아니다 — 바꿔치기면 마지막이 0 이
    // 된다
    eq(Mtf.transform(s("CBAB")), b('C', 'C', 'C', 1), "옮기기");
  }

  private static void testHuffman() {
    long[] f = new long[256];
    f[0] = 5;
    f[1] = 2;
    f[2] = 1;
    int[] l = Huffman.codeLengths(f, Huffman.MAX_LENGTH);
    check(l[0] == 1 && l[1] == 2 && l[2] == 2, "5,2,1 → 1,2,2");

    long[] g = new long[256];
    for (int i = 0; i < 7; i++) {
      g[i] = 1;
    }
    int[] l7 = Huffman.codeLengths(g, Huffman.MAX_LENGTH);
    check(l7[0] == 3 && l7[5] == 3 && l7[6] == 2, "같은 빈도 일곱");

    int[] rfc = new int[256];       // RFC 1951 §3.2.2 의 예
    int[] want = {3, 3, 3, 3, 3, 2, 4, 4};
    System.arraycopy(want, 0, rfc, 0, want.length);
    int[] codes = Huffman.canonicalCodes(rfc);
    check(codes[0] == 0b010 && codes[5] == 0b00 && codes[7] == 0b1111,
        "캐노니컬 부호");
  }

  private static void testLzss() {
    eq(Lzss.encode(s("A")), b(0x01, 0x00, 'A'), "리터럴 하나");
    eq(Lzss.encode(s("AAAA")), b(0x04, 0x40, 'A', 0x00, 0x00, 0x00),
        "첫 일치");
    // 거리 1 짜리 긴 일치 — arraycopy 로 한 번에 옮기면 여기서 깨진다
    byte[] run = repeat('A', 1000);
    eq(Lzss.decode(Lzss.encode(run)), run, "겹치는 일치");
    check(throwsCodec(
        () -> Lzss.decode(b(0x03, 0x80, 0x00, 0x01, 0x00))),
        "시작보다 먼 거리 거절");
  }

  private static void testLzw() {
    eq(Lzw.encode(s("A")), b(0x01, 0x20, 0xC0, 0x40), "한 바이트");
    // 사전이 두 번 넘게 꽉 차는 크기 — 폭 확장의 한 칸 지연을 밟는다
    byte[] big = pseudo(200000, 131, 7);
    eq(Lzw.decode(Lzw.encode(big)), big, "사전 되감기");
  }

  private static void testRangecoder() {
    byte[] src = pseudo(1000, 37, 11);
    byte[] out = RangeCoder.encode(src);
    int head = Varint.put(src.length).length;
    check(out[head] == 0, "코더 스트림의 첫 바이트는 늘 0");
    eq(RangeCoder.decode(out), src, "레인지 코더 왕복");
    byte[] bad = out.clone();
    bad[head] = 1;
    check(throwsCodec(() -> RangeCoder.decode(bad)), "첫 바이트 검사");
  }

  private static void testBwt() {
    int[] primary = new int[1];
    byte[] l = Bwt.transformBlock(s("banana"), primary);
    eq(l, s("nnbaaa"), "banana 의 L 열");
    check(primary[0] == 3, "primary 는 3");
    eq(Bwt.inverseBlock(l, primary[0]), s("banana"), "역변환");
    // 모든 회전이 같다 — 동점은 시작 위치 오름차순이라 primary 가 0
    Bwt.transformBlock(repeat(0, 64), primary);
    check(primary[0] == 0, "동점 규칙");
  }

  private static void testDeflate() {
    eq(Deflate.deflateRaw(new byte[0]), b(0x03, 0x00), "빈 입력");
    check(throwsCodec(() -> Inflate.inflateRaw(b(0x07, 0x00))),
        "BTYPE 11 거절");
    check(throwsCodec(
        () -> Inflate.inflateRaw(b(0x01, 0x01, 0x00, 0x00, 0x00, 'A'))),
        "NLEN 불일치 거절");
    byte[] src = pseudo(50000, 37, 11);
    eq(Inflate.inflateRaw(Deflate.deflateRaw(src)), src,
        "deflate 왕복");
    eq(Containers.zlibDecompress(Containers.zlibCompress(src)), src,
        "zlib 왕복");
    eq(Containers.gzipDecompress(Containers.gzipCompress(src)), src,
        "gzip 왕복");
    byte[] gz = Containers.gzipCompress(s("hi"));
    check(gz[4] == 0 && gz[5] == 0 && gz[6] == 0 && gz[7] == 0,
        "MTIME 은 0 이어야 재현된다");
    byte[] broken = gz.clone();
    int last = broken.length - 5;
    broken[last] = (byte) (broken[last] ^ 0xFF);
    check(throwsCodec(() -> Containers.gzipDecompress(broken)),
        "CRC 검사");
  }

  private static void testRoundTrips() {
    byte[][] cases = {new byte[0], s("A"), repeat(0, 5000),
        pseudo(20000, 37, 11), pseudo(70000, 131, 3)};
    for (Registry.Entry e : Registry.ENTRIES) {
      for (byte[] src : cases) {
        byte[] enc = e.encode.apply(src);
        eq(e.decode.apply(enc), src, e.name + " 왕복 " + src.length);
      }
    }
  }

  public static void main(String[] args) {
    Console.useUtf8();
    testBitio();
    testIntcode();
    testRle();
    testMtf();
    testHuffman();
    testLzss();
    testLzw();
    testRangecoder();
    testBwt();
    testDeflate();
    testRoundTrips();
    System.out.printf("자바 시험 — 검사 %d건 · 실패 %d건%n",
        checks, failures);
    if (failures > 0) {
      System.exit(1);
    }
  }
}
