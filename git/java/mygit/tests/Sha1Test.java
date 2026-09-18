package mygit.tests;

import static mygit.tests.Check.eq;

import java.security.MessageDigest;
import java.util.List;
import java.util.Map;
import mygit.Sha1;

// sha1 의 시험 — SPEC.md §2 · 부록 A 1단계.
//
// 기준은 golden/sha1.tsv 100줄이다. sha1 칸은 coreutils sha1sum 이,
// blob 칸은 진짜 git hash-object 가 낸 값이다. MessageDigest 는 답을
// 맞춰 보는 두 번째 증인으로만 쓴다 — 구현이 그것을 부르면 이 시험은
// 아무것도 증명하지 않는다(SPEC.md §2 첫 문단).
final class Sha1Test {
  private Sha1Test() {}

  private static List<Map<String, String>> vectors() throws Exception {
    return Golden.tsv("sha1.tsv");
  }

  private static byte[] witness(byte[] d) throws Exception {
    return MessageDigest.getInstance("SHA-1").digest(d);
  }

  static void s2_hundredVectorsMatchSha1sum() throws Exception {
    eq(100, vectors().size());
    for (var row : vectors()) {
      byte[] data = Golden.make(row.get("recipe"));
      String name = row.get("name");
      eq(Integer.parseInt(row.get("len")), data.length, name);
      eq(row.get("sha1"), Sha1.sha1Hex(data), name);
    }
  }

  static void s2_rawDigestIsTwentyBytes() throws Exception {
    byte[] d = Sha1.sha1("abc".getBytes());
    eq(20, d.length);
    eq(witness("abc".getBytes()), d);
  }

  static void s2_paddingBoundariesAgreeWithMessageDigest()
      throws Exception {
    // 55 바이트까지는 덧붙임이 한 블록에 들어가고 56 부터 넘친다
    for (int n = 0; n < 200; n++) {
      byte[] data = new byte[n];
      for (int i = 0; i < n; i++) data[i] = (byte) (i * 7);
      eq(witness(data), Sha1.sha1(data), n);
    }
  }

  static void s2_updateInOddChunksEqualsOneShot() throws Exception {
    byte[] data = Golden.make("counter:100000");
    for (int size : new int[] {1, 3, 63, 64, 65, 1000, 99999}) {
      Sha1 h = new Sha1();
      for (int k = 0; k < data.length; k += size) {
        h.update(data, k, Math.min(size, data.length - k));
      }
      eq(Sha1.sha1(data), h.digest(), size);
    }
  }

  static void s2_digestTwiceIsStable() {
    Sha1 h = new Sha1().update("git".getBytes());
    eq(h.digest(), h.digest());
  }

  static void s2_headerPlusBodyIsTheBlobName() throws Exception {
    // blob 이름 = SHA-1("blob <크기>\0" + 몸) — 머리를 붙이는 일은
    // §4 의 몫이지만, 여기서 숫자가 맞으면 SHA-1 쪽은 끝난 것이다.
    for (var row : vectors()) {
      byte[] data = Golden.make(row.get("recipe"));
      byte[] head = ("blob " + data.length + "\0").getBytes();
      byte[] all = new byte[head.length + data.length];
      System.arraycopy(head, 0, all, 0, head.length);
      System.arraycopy(data, 0, all, head.length, data.length);
      eq(row.get("blob"), Sha1.sha1Hex(all), row.get("name"));
    }
  }
}
