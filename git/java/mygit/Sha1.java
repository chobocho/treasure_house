package mygit;

import java.nio.ByteBuffer;
import java.util.HexFormat;

// SHA-1 을 손으로 (SPEC.md §2 · FIPS 180-4).
//
// git 의 모든 객체 이름이 이 함수의 출력이다. MessageDigest 를 부르면
// 한 줄이지만 그러면 "40글자 이름이 어디서 오나" 가 가려진다. 한 블록
// (64바이트) = 80라운드, 전체 O(n) 시간, O(1) 추가 공간.
//
// Java 의 int 는 32비트 2의 보수라 덧셈이 저절로 mod 2³² 로 넘친다 —
// Python 의 & MASK, TS 의 | 0 자리가 여기서는 비어 있다. 부호 없는
// 오른쪽 이동만 >>> 로 조심하면 된다(Integer.rotateLeft 가 해 준다).
public final class Sha1 {
  // 초기값 — FIPS 180-4 §5.3.1. 라운드 상수는 compress 안에.
  private final int[] h = {0x67452301, 0xefcdab89, 0x98badcfe,
      0x10325476, 0xc3d2e1f0};
  private final byte[] buf = new byte[64];
  private int used;
  private long total;

  // 64바이트 한 블록(b[off‥off+64))으로 상태 다섯 개를 갱신한다.
  private static void compress(int[] h, byte[] b, int off) {
    int[] w = new int[80];
    ByteBuffer.wrap(b, off, 64).asIntBuffer().get(w, 0, 16);
    for (int t = 16; t < 80; t++) {
      w[t] = Integer.rotateLeft(w[t - 3] ^ w[t - 8] ^ w[t - 14]
          ^ w[t - 16], 1);
    }
    int a = h[0], bb = h[1], c = h[2], d = h[3], e = h[4];
    for (int t = 0; t < 80; t++) {
      // f + 라운드 상수 — 20라운드마다 함수와 상수가 바뀐다
      int f = t < 20 ? ((bb & c) | (~bb & d)) + 0x5a827999
          : t < 40 ? (bb ^ c ^ d) + 0x6ed9eba1
          : t < 60 ? ((bb & c) | (bb & d) | (c & d)) + 0x8f1bbcdc
          : (bb ^ c ^ d) + 0xca62c1d6;
      int tmp = Integer.rotateLeft(a, 5) + f + e + w[t];
      e = d;
      d = c;
      c = Integer.rotateLeft(bb, 30);
      bb = a;
      a = tmp;
    }
    h[0] += a;
    h[1] += bb;
    h[2] += c;
    h[3] += d;
    h[4] += e;
  }

  public Sha1 update(byte[] data) {
    return update(data, 0, data.length);
  }

  // 스트리밍 — 인덱스와 팩의 끝 체크섬을 파일을 읽어 가며 셀 때 쓴다.
  public Sha1 update(byte[] data, int off, int len) {
    total += len;
    while (len > 0) {
      int n = Math.min(64 - used, len);
      System.arraycopy(data, off, buf, used, n);
      used += n;
      off += n;
      len -= n;
      if (used == 64) {
        compress(h, buf, 0);
        used = 0;
      }
    }
    return this;
  }

  // 덧붙임: 0x80, 0 들, 비트 길이(빅 엔디언 64비트). 상태를 건드리지
  // 않는 사본에서 마무리하므로 두 번 불러도 같다. 55바이트까지는
  // 덧붙임이 한 블록에, 56바이트부터는 두 블록에 들어간다.
  public byte[] digest() {
    int[] s = h.clone();
    byte[] tail = new byte[used < 56 ? 64 : 128];
    System.arraycopy(buf, 0, tail, 0, used);
    tail[used] = (byte) 0x80;
    ByteBuffer.wrap(tail).putLong(tail.length - 8, total * 8);
    for (int k = 0; k < tail.length; k += 64) compress(s, tail, k);
    ByteBuffer out = ByteBuffer.allocate(20);
    for (int v : s) out.putInt(v);
    return out.array();
  }

  // 바이트열의 SHA-1, 20바이트.
  public static byte[] sha1(byte[] data) {
    return new Sha1().update(data).digest();
  }

  // 소문자 16진 40글자 — git 이 화면에 찍는 객체 이름의 꼴.
  public static String sha1Hex(byte[] data) {
    return HexFormat.of().formatHex(sha1(data));
  }
}
