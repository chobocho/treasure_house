package mygit.tests;

import static java.nio.charset.StandardCharsets.UTF_8;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import mygit.Cli;
import mygit.Fs;

// 임시 디렉터리 하나 — 작업 트리 root 는 그 안의 w/. repo 면 .git
// 뼈대를 손으로 만든다(init 은 5단계의 일이다). try-with-resources
// 로 쓰면 끝에서 지운다.
final class Sandbox implements AutoCloseable {
  static final Map<String, String> IDENT = Map.of(
      "GIT_AUTHOR_NAME", "A U Thor",
      "GIT_AUTHOR_EMAIL", "author@example.com",
      "GIT_AUTHOR_DATE", "1700000000 +0900",
      "GIT_COMMITTER_NAME", "C O Mitter",
      "GIT_COMMITTER_EMAIL", "committer@example.com",
      "GIT_COMMITTER_DATE", "1700000000 +0900");

  final String tmp;
  final String root;
  final String gitdir;
  final Map<String, String> env = new HashMap<>(System.getenv());

  Sandbox(boolean repo) throws Exception {
    tmp = Golden.tempdir();
    root = Fs.join(tmp, "w");
    gitdir = Fs.join(root, ".git");
    Fs.mkdirs(root);
    if (repo) {
      for (String d : List.of("objects/pack", "refs/heads",
          "refs/tags")) {
        Fs.mkdirs(Fs.join(gitdir, d));
      }
      Fs.write(Fs.join(gitdir, "HEAD"),
          "ref: refs/heads/main\n".getBytes());
    }
    // 위로 올라가다 이 덱의 저장소를 찾지 않게 (SPEC.md §1.1)
    env.put("GIT_CEILING_DIRECTORIES", tmp);
    env.putAll(IDENT);
  }

  @Override
  public void close() throws java.io.IOException {
    Golden.rmTree(tmp);
  }

  Cli.Result mygit(byte[] stdin, String... args) {
    return Cli.run(List.of(args), root, env, stdin);
  }

  Cli.Result mygit(String... args) {
    return mygit(new byte[0], args);
  }

  // 표준 출력을 글자로 — 짧은 단언용
  String out(String... args) {
    return new String(mygit(args).out(), UTF_8);
  }

  // (코드, 표준 오류 첫 줄) — golden/errors.tsv 와 견주는 꼴
  static String firstLine(Cli.Result r) {
    return r.code() + " " + new String(r.err(), UTF_8).split("\n")[0];
  }

  void put(String name, byte[] data) {
    Fs.write(Fs.join(root, name), data);
  }

  void plant(String oid) throws Exception {
    ObjectsTest.plant(gitdir, oid);
  }
}
