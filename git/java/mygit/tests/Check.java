package mygit.tests;

import java.io.FileOutputStream;
import java.io.FileDescriptor;
import java.io.PrintStream;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.Comparator;
import java.util.HexFormat;
import mygit.GitError;

// 결정 12 — JUnit 없이. 시험 하나 = 이름이 s<절 번호> 로 시작하는
// static 메서드 하나. 단언이 틀리면 AssertionError 를 던지고, suite
// 가 그것을 세어 둔다. 실패가 하나라도 있으면 RunTests 가 1 로 끝난다.
final class Check {
  interface Body { void run() throws Exception; }

  @SuppressWarnings("serial")
  static final class Skip extends RuntimeException {
    Skip(String why) { super(why); }
  }

  // 로캘이 ASCII 여도 한글 실패 문장이 보이게 UTF-8 로 직접 쓴다
  static final PrintStream OUT = new PrintStream(
      new FileOutputStream(FileDescriptor.out), true,
      StandardCharsets.UTF_8);
  static int passed, failed, skipped;

  private Check() {}

  static void test(String name, Body body) {
    try {
      body.run();
      passed++;
    } catch (Skip s) {
      skipped++;
      OUT.println("  건너뜀 " + name + " — " + s.getMessage());
    } catch (Throwable t) {
      failed++;
      OUT.println("  실패 " + name + " — " + t);
    }
  }

  // 클래스의 s<숫자>… 메서드를 이름 차례로 돈다
  static void suite(Class<?> c) {
    Method[] ms = c.getDeclaredMethods();
    Arrays.sort(ms, Comparator.comparing(Method::getName));
    for (Method m : ms) {
      if (!m.getName().matches("s\\d.*")) continue;
      test(c.getSimpleName() + "." + m.getName(), () -> {
        try {
          m.invoke(null);
        } catch (InvocationTargetException e) {
          if (e.getCause() instanceof Exception x) throw x;
          throw (Error) e.getCause();
        }
      });
    }
  }

  static void skip(String why) {
    throw new Skip(why);
  }

  static void ok(boolean cond, Object what) {
    if (!cond) throw new AssertionError(what);
  }

  // byte[] 는 내용으로 견준다. 실패 문장에 둘을 다 싣는다.
  static void eq(Object want, Object got, Object... what) {
    boolean same = want instanceof byte[] w && got instanceof byte[] g
        ? Arrays.equals(w, g) : java.util.Objects.equals(want, got);
    if (!same) {
      throw new AssertionError(Arrays.toString(what) + " 기대 <"
          + show(want) + "> 실제 <" + show(got) + ">");
    }
  }

  private static Object show(Object o) {
    return o instanceof byte[] b ? HexFormat.of().formatHex(b) : o;
  }

  // body 가 **진짜** GitError 를 던지는가. 껍데기도 GitError 를
  // 던지므로 그냥 "예외가 났나" 로 보면 구현 전에 이미 통과한다 —
  // 거짓 초록이다. 코드 99 는 "아직 안 짰다" 라서 여기서 떨어뜨린다.
  static GitError gitError(Body body) throws Exception {
    try {
      body.run();
    } catch (GitError e) {
      ok(e.code != 99, "not implemented");
      return e;
    }
    throw new AssertionError("GitError 가 나지 않았다");
  }
}
