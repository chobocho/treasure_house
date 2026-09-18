package mygit;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.file.FileAlreadyExistsException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.nio.file.StandardOpenOption;
import java.util.ArrayList;
import java.util.List;
import java.util.stream.Stream;

// 파일 시스템 몇 가지를 한 줄로. 경로는 바이트 문자열(Main.byteNames)
// 이고, IOException 은 UncheckedIOException 으로 바꿔 던진다 — 모든
// 메서드에 throws 를 달지 않으려고. Cli 가 그것을 받아 오류로 찍는다.
public final class Fs {
  private Fs() {}

  public static String join(String first, String... more) {
    return Path.of(first, more).toString();
  }

  public static boolean exists(String p) {
    return Files.exists(Path.of(p));
  }

  public static boolean isDir(String p) {
    return Files.isDirectory(Path.of(p));
  }

  public static byte[] read(String p) {
    try {
      return Files.readAllBytes(Path.of(p));
    } catch (IOException e) {
      throw new UncheckedIOException(e);
    }
  }

  // 없으면 null — 참조 파일처럼 "없음" 이 흔한 답인 곳에서 쓴다
  public static byte[] readOrNull(String p) {
    return Files.isRegularFile(Path.of(p)) ? read(p) : null;
  }

  public static void write(String p, byte[] data) {
    try {
      Files.write(Path.of(p), data);
    } catch (IOException e) {
      throw new UncheckedIOException(e);
    }
  }

  public static void mkdirs(String p) {
    try {
      Files.createDirectories(Path.of(p));
    } catch (IOException e) {
      throw new UncheckedIOException(e);
    }
  }

  // 있으면 지운다(파일 하나)
  public static void delete(String p) {
    try {
      Files.deleteIfExists(Path.of(p));
    } catch (IOException e) {
      throw new UncheckedIOException(e);
    }
  }

  // <경로>.lock 에 쓰고 이름을 바꿔 넣는다(SPEC.md §6.1 · §7.4). 쓰는
  // 도중에 죽어도 옛 파일이 멀쩡하고, .lock 이 이미 있으면 누군가
  // 쓰는 중이라는 뜻이다.
  public static void writeLocked(String path, byte[] data) {
    Path p = Path.of(path);
    Path lock = Path.of(path + ".lock");
    try {
      Files.createDirectories(p.getParent());
      Files.write(lock, data, StandardOpenOption.CREATE_NEW,
          StandardOpenOption.WRITE);
      Files.move(lock, p, StandardCopyOption.REPLACE_EXISTING);
    } catch (FileAlreadyExistsException e) {
      throw new GitError("fatal: mygit: unable to lock " + path);
    } catch (IOException e) {
      throw new UncheckedIOException(e);
    }
  }

  // 디렉터리 안의 이름들, 바이트 차례. 디렉터리가 아니면 빈 목록.
  public static List<String> list(String dir) {
    if (!isDir(dir)) return new ArrayList<>();
    try (Stream<Path> s = Files.list(Path.of(dir))) {
      return new ArrayList<>(s.map(x -> x.getFileName().toString())
          .sorted().toList());
    } catch (IOException e) {
      throw new UncheckedIOException(e);
    }
  }
}
