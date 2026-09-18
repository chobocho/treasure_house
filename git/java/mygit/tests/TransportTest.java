package mygit.tests;

import static java.nio.charset.StandardCharsets.ISO_8859_1;
import static java.nio.charset.StandardCharsets.UTF_8;
import static mygit.tests.Check.eq;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HexFormat;
import java.util.List;
import java.util.Map;
import mygit.Cli;
import mygit.Fs;
import mygit.Objects;
import mygit.Refs;
import mygit.Transport;

// 전송의 시험 — SPEC.md §14, 12단계 "pkt-line 으로 진짜 git 과 대화".
//
// fetch-pack 은 진짜 git upload-pack 을 자식으로 띄워 말한다(PLAN.md
// §9 결정 8 — 서버는 git 이다). golden/pkt/<경우>.log 는 SPEC §14.3 의
// 요청을 그대로 보냈을 때 git 이 돌려준 대화의 기록이고, mygit 의
// 기록은 글자까지 같아야 한다. 받은 팩 바이트와 표준 출력도 같아야
// 한다. 멍청한 clone 은 golden/scen/clone.scn 이 장면 시험으로 본다.
final class TransportTest {
  private TransportTest() {}

  static void s14_1_lengthCountsItself() {
    eq("0006a\n", new String(Transport.pktLine("a\n".getBytes()),
        ISO_8859_1));
    eq("0004", new String(Transport.pktLine(new byte[0]), ISO_8859_1));
    eq("fff0", new String(Transport.pktLine(new byte[65516]), 0, 4,
        ISO_8859_1));
  }

  static void s14_3_renderLikeTheGoldenLog() {
    eq("0014command=ls-refs\\n",
        Transport.render("command=ls-refs\n".getBytes()));
  }

  static void copyTree(Path src, Path dst) throws Exception {
    Files.createDirectories(dst.getParent());
    try (var s = Files.walk(src)) {
      for (Path p : s.toList()) {
        Files.copy(p, dst.resolve(src.relativize(p)));
      }
    }
  }

  // 원본 src/ 와 빈 저장소 w/ 를 만들고 fetch-pack 을 한 번 돈다.
  // → [표준 출력, 대화 기록, 받은 팩 바이트]. 받는 쪽의 .git 을 fn 이
  // 끝난 뒤 본다.
  interface AfterFetch {
    void check(Sandbox sb, Cli.Result r, String log) throws Exception;
  }

  static void fetch(String kase, AfterFetch after) throws Exception {
    try (var sb = new Sandbox(false)) {
      Path src = Path.of(sb.tmp, "src");
      copyTree(Path.of(Golden.path("pkt", "src", "git")),
          src.resolve(".git"));
      Fs.mkdirs(src.resolve(".git/objects/pack").toString());
      Fs.mkdirs(src.resolve(".git/refs/tags").toString());
      sb.mygit("init");
      String[] args = new String(Golden.read("pkt", kase + ".args"),
          UTF_8).split("\n", -1);
      if (!args[1].isEmpty()) {
        // 가진 값 = 로컬 참조. 원본의 객체를 넣고 참조를 세운다
        Golden.rmTree(Fs.join(sb.gitdir, "objects"));
        copyTree(src.resolve(".git/objects"),
            Path.of(sb.gitdir, "objects"));
        Refs.updateRef(sb.gitdir, "refs/heads/old", args[1], null,
            "test", "T <t@t> 0 +0000");
      }
      String log = Fs.join(sb.tmp, kase + ".log");
      Map<String, String> env = new HashMap<>(sb.env);
      env.put("MYGIT_PKT_LOG", log);
      List<String> cmd = new ArrayList<>(List.of("fetch-pack",
          src.toString()));
      cmd.addAll(List.of(args[0].split(" ")));
      Cli.Result r = Cli.run(cmd, sb.root, env, new byte[0]);
      after.check(sb, r, new String(Fs.read(log), UTF_8));
    }
  }

  static void s14_3_conversationMatchesGit() throws Exception {
    for (String kase : List.of("full", "two-refs", "have-first")) {
      fetch(kase, (sb, r, log) -> {
        eq(0, r.code(), kase, new String(r.err(), UTF_8));
        eq(0, r.err().length, kase);
        eq(Golden.read("pkt", kase + ".stdout"), r.out(), kase);
        eq(new String(Golden.read("pkt", kase + ".log"), UTF_8), log,
            kase);
      });
    }
  }

  static void s14_3_receivedPackIsStoredAndReadable() throws Exception {
    fetch("full", (sb, r, log) -> {
      byte[] want = Golden.read("pkt", "full.pack");
      String name = "pack-" + HexFormat.of().formatHex(want,
          want.length - 20, want.length) + ".pack";
      eq(want, Fs.read(Fs.join(sb.gitdir, "objects", "pack", name)));
      String head = new String(Golden.read("pkt", "full.stdout"),
          UTF_8).split(" ")[0];
      eq("commit", Objects.readObject(sb.gitdir, head).type());
    });
  }
}
