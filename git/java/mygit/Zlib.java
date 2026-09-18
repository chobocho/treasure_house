package mygit;

import java.io.ByteArrayOutputStream;
import java.util.zip.Adler32;
import java.util.zip.DataFormatException;
import java.util.zip.Deflater;
import java.util.zip.Inflater;

// zlib 겉옷 (SPEC.md §3) — 느슨한 객체와 팩 항목이 입는 옷.
//
// Java 는 java.util.zip 의 Deflater·Inflater 를 쓴다(SPEC.md §3.1 의
// 표). 이 클래스가 따로 있는 까닭은 둘이다. 하나, 다섯 언어가 같은
// 이름(compress·decompress·decompressPrefix·adler32)으로 부르게
// 하려고. 둘, 팩 안에서는 "스트림이 몇 바이트에서 끝나는가" 가
// 필요한데, Inflater 는 스트림 끝에서 멈추고 getRemaining() 으로 안
// 먹은 입력의 길이를 알려 준다 — 준 길이에서 빼면 먹은 수다.
public final class Zlib {
  // git 의 느슨한 객체 기본값과 같은 "가장 빠르게"
  public static final int LEVEL = 1;

  private Zlib() {}

  public record Inflated(byte[] data, int used) {}

  public static byte[] compress(byte[] data) {
    Deflater d = new Deflater(LEVEL);
    d.setInput(data);
    d.finish();
    ByteArrayOutputStream out = new ByteArrayOutputStream();
    byte[] buf = new byte[8192];
    while (!d.finished()) out.write(buf, 0, d.deflate(buf));
    d.end();
    return out.toByteArray();
  }

  // data[start:] 에서 zlib 스트림 하나를 풀어 (바이트, 먹은 수).
  //
  // 먹은 수에는 머리 2바이트와 Adler-32 꼬리 4바이트가 들어간다 —
  // 다음 팩 항목은 정확히 거기서 시작한다. Adler-32 가 틀리면
  // Inflater 가 DataFormatException 을 던진다. O(스트림 길이).
  public static Inflated decompressPrefix(byte[] data, int start) {
    Inflater inf = new Inflater();
    inf.setInput(data, start, data.length - start);
    ByteArrayOutputStream out = new ByteArrayOutputStream();
    byte[] buf = new byte[8192];
    try {
      while (!inf.finished()) {
        int n = inf.inflate(buf);
        if (n == 0 && !inf.finished()
            && (inf.needsInput() || inf.needsDictionary())) {
          throw new GitError("fatal: mygit: truncated zlib stream");
        }
        out.write(buf, 0, n);
      }
      return new Inflated(out.toByteArray(),
          data.length - start - inf.getRemaining());
    } catch (DataFormatException e) {
      throw new GitError("fatal: mygit: corrupt zlib stream");
    } finally {
      inf.end();
    }
  }

  // 스트림 하나를 끝까지. 뒤에 남는 바이트가 있으면 오류다.
  public static byte[] decompress(byte[] data) {
    Inflated r = decompressPrefix(data, 0);
    if (r.used() != data.length) {
      throw new GitError("fatal: mygit: garbage after zlib stream");
    }
    return r.data();
  }

  public static long adler32(byte[] data) {
    Adler32 a = new Adler32();
    a.update(data);
    return a.getValue();
  }
}
