package compresslib;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;

/**
 * compresslib 명령줄 도구 (Java) — 다섯 언어가 같은 사용법을 갖는다.
 *
 * <pre>
 *   java -cp build/java compresslib.Main \
 *       &lt;알고리즘&gt; enc|dec &lt;입력&gt; &lt;출력&gt;
 *   java -cp build/java compresslib.Main batch &lt;작업파일&gt;
 *   java -cp build/java compresslib.Main list
 * </pre>
 *
 * <p>batch 가 있는 이유는 파서티 검사다. 건마다 JVM 을 띄우면 조합 수천
 * 건에 몇 분이 간다 — 이 기계는 JVM 을 한 번에 하나만 띄울 수 있어 더
 * 그렇다.
 */
public final class Main {
  private Main() {}

  /** 실패하면 사람이 읽을 문장을, 성공하면 빈 문자열을 돌려준다. */
  static String runOne(String algo, String mode, String in,
      String out) {
    Registry.Entry e = Registry.find(algo);
    if (e == null) {
      return "모르는 알고리즘: " + algo;
    }
    if (!mode.equals("enc") && !mode.equals("dec")) {
      return "enc 또는 dec 이어야 한다: " + mode;
    }
    if (mode.equals("enc") && e.encode == null) {
      return algo + " 는 복호기만 있다";
    }
    byte[] data;
    try {
      data = Files.readAllBytes(Path.of(in));
    } catch (IOException ex) {
      return "입력을 못 읽는다: " + in;
    }
    byte[] result;
    try {
      result = mode.equals("enc") ? e.encode.apply(data)
                                  : e.decode.apply(data);
    } catch (CodecException ex) {
      return algo + " " + mode + " 실패: " + ex.getMessage();
    }
    try {
      Files.write(Path.of(out), result);
    } catch (IOException ex) {
      return "출력을 못 쓴다: " + out;
    }
    return "";
  }

  static int batch(String jobPath) throws IOException {
    List<String> lines = Files.readAllLines(Path.of(jobPath),
        StandardCharsets.UTF_8);
    StringBuilder sb = new StringBuilder();
    for (String raw : lines) {
      String line = raw.trim();
      if (line.isEmpty() || line.startsWith("#")) {
        continue;
      }
      String[] parts = line.split("\\s+");
      if (parts.length != 4) {
        sb.append("FAIL 칸이 4개가 아니다\n");
        continue;
      }
      String msg = runOne(parts[0], parts[1], parts[2], parts[3]);
      sb.append(msg.isEmpty() ? "OK\n" : "FAIL " + msg + "\n");
    }
    System.out.print(sb);
    return 0;
  }

  public static void main(String[] args) throws IOException {
    Console.useUtf8();
    if (args.length == 1 && args[0].equals("list")) {
      for (Registry.Entry e : Registry.ENTRIES) {
        System.out.println(e.name);
      }
      return;
    }
    if (args.length == 2 && args[0].equals("batch")) {
      System.exit(batch(args[1]));
    }
    if (args.length != 4) {
      System.err.println(
          "사용법: Main <알고리즘> enc|dec <입력> <출력>");
      System.err.println("        Main batch <작업파일>");
      System.exit(2);
    }
    String msg = runOne(args[0], args[1], args[2], args[3]);
    if (!msg.isEmpty()) {
      System.err.println(msg);
      System.exit(1);
    }
  }
}
