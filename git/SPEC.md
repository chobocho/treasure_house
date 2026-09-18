# SPEC — 다섯 mygit 이 함께 지키는 약속

이 문서는 부록 A 의 미니 Git(`mygit`)을 Python·TypeScript·Go·Java·C++
다섯 언어로 만들 때 **모두가 똑같이 지켜야 하는 것**을 전부 적는다.
다섯 시험 묶음이 이 문서의 절 번호(§)를 인용한다. 코드보다 먼저 쓰였고,
코드가 이 문서와 어긋나면 코드가 틀린 것이다.

그리고 이 문서 위에 심판이 하나 더 있다 — **이 기계에 설치된 git 2.55.0**.
이 문서가 git 의 동작을 옮겨 적은 자리에서 git 과 어긋나면, 틀린 것은
이 문서다. 고치는 쪽도 이 문서다(PLAN.md §0.3·§0.6).

- 바이트 예시는 손으로 쓰지 않았다. `<!--EX 이름-->` 블록은 전부
  `tools/spec_examples.py` 가 진짜 git 을 돌려 뜬 것이고,
  `make spec-check` 가 이 문서의 블록과 다시 뜬 결과를 글자 단위로 대조한다.
- 시험의 기준 바이트는 `golden/` 에 있고, 그것도 진짜 git 이 만든다
  (PLAN.md §5 3단계). 이 문서는 무엇을 맞춰야 하는지를, `golden/` 은
  맞췄는지 볼 답을 갖고 있다.
- "git 은 이렇게 하지만 mygit 은 줄였다" 는 자리는 **줄임**이라고 적었다.
  줄인 자리에서 mygit 의 출력은 git 과 다르고, 그 차이는 덱의 부록 A 에서도
  그대로 말한다.

---

## 0. 범위

### 0.1 명령

| 명령 | 하는 일 | 단계(PLAN.md §3.1) |
|---|---|---|
| `init [<dir>]` | 빈 저장소 | 5 |
| `hash-object [-w] [-t <type>] (<file> \| --stdin)` | 객체 이름 계산·쓰기 | 3 |
| `cat-file (-t \| -s \| -p) <object>` | 객체 꺼내 보기 | 3 |
| `add <pathspec>…` | 인덱스에 올리기 | 6 |
| `rm --cached <path>…` | 인덱스에서만 내리기 | 6 |
| `status` | `git status --porcelain` 과 같은 짧은 상태 | 6 |
| `write-tree` | 인덱스 → 트리 | 4 |
| `commit-tree <tree> [-p <parent>]… -m <msg>…` | 커밋 객체 | 5 |
| `commit -m <msg>…` | 트리를 쓰고 커밋하고 브랜치를 옮긴다 | 5 |
| `log [--oneline] [-n <N>] [<rev>]` | 역사 | 7 |
| `merge-base [--all] <a> <b>` | 공통 조상 | 7 |
| `branch [-d] [<name> [<start>]]` | 브랜치 목록·만들기·지우기 | 5 |
| `switch [-c] <branch>` · `checkout <branch\|commit>` | 작업 트리 바꾸기 | 9 |
| `tag [-a <name> -m <msg> [<rev>]] [<name> [<rev>]]` | 태그 | 5 |
| `reflog [<ref>]` | 참조 로그 보기 | 5 |
| `diff [--cached] [<c1> <c2>]` · `diff --no-index <a> <b>` | 줄 단위 차이 | 8 |
| `merge <branch>` | fast-forward · 3-way · 충돌 | 10 |
| `unpack-pack <pack>` · `verify-pack -v <idx>` · `pack-objects [--delta] <out>` | 팩 읽기·검사·쓰기 | 11 |
| `clone <path> <dir>` · `fetch-pack <path> <ref>…` | 전송 | 12 |

### 0.2 범위 밖 (덱에서는 진짜 git 캡처로만 보인다)

- SHA-256 저장소(`--object-format=sha256`) — mygit 은 SHA-1 만(PLAN.md §9 결정 4).
- `.gitignore`·`.gitattributes`·설정 파일 읽기(작성자도 환경 변수에서만, §1.3).
- 심볼릭 링크·서브모듈의 **작업 트리 쓰기**. 트리에서 읽고 `cat-file -p` 로
  보여 주는 것은 된다(§4.3 의 모드 표).
- 이름 변경 감지, rebase·cherry-pick·stash·reset, 훅, 서명, 원격 설정 해석.
- 서버 쪽 전송(`upload-pack`·`receive-pack`), HTTP·SSH 소켓(결정 8).
- index v4(경로 압축)와 그 밖의 확장 쓰기. 읽을 때는 확장을 건너뛴다(§7.5).

---

## 1. 실행 계약

### 1.1 부르는 법

| 언어 | 짓기 | 부르기 |
|---|---|---|
| Python | 없음 | `PYTHONPATH=git/py python3 -m mygit <명령> …` |
| Go | `make build-go` | `git/build/mygit-go <명령> …` |
| TypeScript | `make build-ts` | `node git/build/ts/src/main.js <명령> …` |
| Java | `make build-java` | `sh tools/flock_java.sh java -cp git/build/java mygit.Main <명령> …` |
| C++ | `make build-cpp` | `git/build/mygit-cpp <명령> …` |

현재 디렉터리에서 위로 올라가며 `.git` 디렉터리를 찾는다(git 과 같다).
환경 변수 `GIT_CEILING_DIRECTORIES`(콜론으로 가른 절대 경로들)가 있으면 **그
디렉터리 안으로는 올라가지 않는다** — 현재 디렉터리 자신은 언제나 본다. 이
덱의 실험과 시험은 모두 이 변수를 "장면 뿌리의 부모" 로 두고 돈다. 그러지 않으면
저장소가 아닌 디렉터리에서 부른 mygit·git 이 위로 올라가 이 덱의 저장소
(treasure_house)를 찾아 버린다.
작업 트리의 뿌리는 그 `.git` 의 부모다. 경로 인자는 **뿌리에서 부른다고
가정한다** — 하위 디렉터리에서 부른 경우의 경로 변환은 줄임이다.
찾지 못하면 §1.4 의 첫 번째 오류로 끝난다. `init`·`hash-object`(`-w` 없이)·
`diff --no-index` 는 저장소가 없어도 된다.

### 1.2 출력

- 정상 출력은 표준 출력, 오류는 표준 오류, 둘 다 UTF-8 이고 줄 끝은 `\n`.
- 색을 쓰지 않는다. 페이저를 부르지 않는다. 단말인지 아닌지로 동작을 바꾸지 않는다.
- git 이 표준 오류에 쓰는 안내(예: `Switched to branch 'x'`)는 mygit 도
  표준 오류에 쓴다. 명령마다 어느 쪽인지는 §9 의 표가 정한다.
- 객체 이름의 줄임은 **언제나 7글자**다. git 은 저장소가 커지면 더 길게 쓰지만
  (core.abbrev=auto) 이 덱의 실험 저장소는 작아서 git 도 7글자를 쓴다. 줄임.

### 1.3 환경 변수 — 설정 파일을 읽지 않는다

작성자·커미터는 **환경 변수에서만** 온다. 시계를 읽지 않는다.

| 변수 | 쓰는 곳 |
|---|---|
| `GIT_AUTHOR_NAME` · `GIT_AUTHOR_EMAIL` · `GIT_AUTHOR_DATE` | 커밋의 author |
| `GIT_COMMITTER_NAME` · `GIT_COMMITTER_EMAIL` · `GIT_COMMITTER_DATE` | 커밋의 committer, 태그의 tagger, reflog 의 한 줄 |

날짜는 `<초> <±hhmm>` 한 꼴만 받는다(예: `1700000000 +0900`,
`tools/gitenv.sh` 가 쓰는 꼴). 필요한 변수가 없거나 꼴이 다르면
`fatal: mygit: <변수 이름> is not set` 또는 `… is not '<seconds> <+hhmm>'` 를
표준 오류에 쓰고 128 로 끝난다. git 은 설정·시계로 채우지만 mygit 은
결정론을 위해 그러지 않는다(PLAN.md §0.9).

### 1.4 오류 계약

git 은 같은 "없는 이름" 이라도 명령마다 다른 문장을 쓴다. mygit 은 아래
표의 오류를 **첫 줄 글자까지, 종료 코드까지** git 과 같게 낸다. 표는 진짜
git 2.55.0 에 `nope` 를 넣어 뜬 것이다(2026-09-18 확인, golden/errors.tsv 가
같은 내용을 시험용으로 갖는다).

| 상황 | 표준 오류 첫 줄 | 코드 |
|---|---|---|
| `.git` 이 없다 | `fatal: not a git repository (or any of the parent directories): .git` | 128 |
| `cat-file -p nope` · `merge-base main nope` | `fatal: Not a valid object name nope` | 128 |
| `commit-tree nope -m x` | `fatal: not a valid object name nope` | 128 |
| `branch x nope` | `fatal: not a valid object name: 'nope'` | 128 |
| `switch nope` | `fatal: invalid reference: nope` | 128 |
| `checkout nope` | `error: pathspec 'nope' did not match any file(s) known to git` | 1 |
| `tag t nope` | `fatal: Failed to resolve 'nope' as a valid ref.` | 128 |
| `merge nope` | `merge: nope - not something we can merge` | 1 |
| `log nope` · `diff nope main` · `reflog nope` | `fatal: ambiguous argument 'nope': unknown revision or path not in the working tree.` | 128 |
| `add nope` · `rm --cached nope` | `fatal: pathspec 'nope' did not match any files` | 128 |
| `hash-object nope` | `fatal: could not open 'nope' for reading: No such file or directory` | 128 |
| `merge` 가 충돌로 멈췄다 | (표준 출력 마지막 줄) `Automatic merge failed; fix conflicts and then commit the result.` | 1 |

`ambiguous argument` 오류 뒤에 git 은 도움말 두 줄을 더 쓴다. mygit 도
같은 두 줄을 쓴다 — 첫 줄만 같고 뒤가 다르면 캡처를 나란히 놓았을 때
독자가 헷갈린다.

```text
Use '--' to separate paths from revisions, like this:
'git <command> [<revision>...] -- [<file>...]'
```

그 밖의 오류는 mygit 만의 것이다 — `fatal: mygit: <무엇이 잘못됐나>` 한 줄에
코드 128. 모르는 명령은 `mygit: '<x>' is not a mygit command.` 에 코드 1,
모르는 옵션은 `fatal: mygit: unknown option '<x>'` 에 코드 128.

### 1.5 경로

경로는 작업 트리 뿌리에서의 상대 경로이고, 구분자는 `/`, 바이트는 UTF-8
그대로다. **비교는 언제나 바이트 비교다**(언어의 문자열 비교·로캘 정렬을
쓰지 않는다 — Java·TypeScript 의 UTF-16 비교는 한글이 섞이면 차례가 다르다).
`.git` 이라는 이름의 항목은 어느 깊이에서든 건너뛴다.

---

## 2. SHA-1

FIPS 180-4 의 SHA-1 을 **다섯 언어 모두 손으로** 짠다(결정 3). 표준
라이브러리의 해시(`hashlib`·`crypto`·`crypto/sha1`·`MessageDigest`)는
시험에서 답을 맞춰 볼 때만 쓴다. C++ 에는 대조할 표준 해시가 없으므로
`golden/sha1.tsv` 가 유일한 기준이다.

- 입력은 바이트열, 출력은 20바이트. 16진 표기는 소문자 40글자.
- 덧붙임: `0x80` 한 바이트, 길이를 448 mod 512 비트에 맞출 만큼의 0,
  원래 길이(비트 수)를 **빅 엔디언 64비트**로. 55·56·63·64·65바이트가 경계다.
- 한 블록 = 64바이트, 80라운드, 상수 `5a827999 6ed9eba1 8f1bbcdc ca62c1d6`,
  초기값 `67452301 efcdab89 98badcfe 10325476 c3d2e1f0`. 모든 덧셈은 mod 2³².
- 스트리밍 API(`update`·`digest`)를 갖춘다 — 인덱스와 팩의 끝 체크섬은
  파일 전체를 한 번에 메모리에 올리지 않고도 셀 수 있어야 한다.
- `golden/sha1.tsv` 는 100줄, 칸은 `name<TAB>len<TAB>recipe<TAB>sha1<TAB>blob`
  이다(빈 입력, 55·56·63·64·65바이트 경계, 1 MB 까지). `recipe` 는 입력을 다시
  만드는 규칙(§2.1), `sha1` 은 **입력 그대로의** SHA-1 로 coreutils
  `sha1sum` 이 낸 값, `blob` 은 같은 입력을 진짜 `git hash-object --stdin` 에
  넣어 얻은 blob 이름이다. 객체 헤더를 붙이는 일은 §4 의 몫이라, 두 칸을
  나눠 두면 "SHA-1 이 틀렸나 헤더가 틀렸나" 가 갈린다.

### 2.1 시험 입력을 만드는 규칙

1 MB 입력을 파일로 커밋하지 않으려고 입력은 규칙으로 적는다. 다섯 언어가
같은 규칙으로 같은 바이트를 만들어야 한다.

| recipe | 바이트 |
|---|---|
| `empty` | 없음 |
| `text:<글자열>` | 그 글자열의 UTF-8 바이트(`\n` 은 줄바꿈 하나) |
| `repeat:<16진 바이트>:<n>` | 그 한 바이트를 n 번 |
| `counter:<n>` | i = 0‥n−1 에 대해 `i mod 251` 한 바이트씩(251 은 소수라 64바이트 블록과 어긋난다) |

git 은 SHA-1 대신 충돌 탐지 SHA-1(sha1dc)을 쓴다. 보통 입력에서 둘의 답은
같다(다른 것은 SHAttered 류 충돌 입력뿐이다 — 14부에서 다룬다).

---

## 3. zlib — 느슨한 객체와 팩 항목의 겉옷

느슨한 객체 파일과 팩의 각 항목은 RFC 1950(zlib) 스트림이다. 속은 RFC 1951
(deflate), 겉은 2바이트 머리(CMF·FLG)와 4바이트 Adler-32 꼬리다.

### 3.1 쓰기

| 언어 | 쓰는 것 |
|---|---|
| Python · TypeScript · Java | 표준 zlib, 압축 수준 1 |
| Go | `compress/zlib`, 압축 수준 1 |
| C++ | **손으로 짠 저장 블록(BTYPE=00)** — 압축하지 않고 65,535바이트씩 싸기만 한다. 머리 `78 01`, 꼬리 Adler-32 |

**압축된 바이트는 다섯 언어가 달라도 된다.** Go 의 deflate 는 zlib 과
다른 구현이고, C++ 은 아예 압축하지 않는다. 같아야 하는 것은 **풀었을 때의
바이트와 그 SHA-1** 이다. git 도 느슨한 객체의 이름을 푼 바이트로 정하므로,
C++ 이 쓴 저장 블록 객체도 진짜 git 이 그대로 읽는다(`golden/stored_ok.txt` 가
그것을 확인한 기록이다 — PLAN.md §3.0).

### 3.2 읽기

- 모든 언어가 **완전한 inflate** 를 해야 한다 — 진짜 git 이 쓴 객체는 고정
  허프만(BTYPE=01)·동적 허프만(BTYPE=10) 블록이다. C++ 은 이것을 손으로
  짠다(RFC 1951 §3.2.5–3.2.7 의 길이·거리 표와 코드 길이 부호).
- 팩 안의 항목은 **스트림이 어디서 끝나는지** 알아야 다음 항목을 읽는다.
  그래서 읽기 API 는 `(풀린 바이트, 먹은 입력 바이트 수)` 를 돌려준다.
  먹은 수에는 Adler-32 꼬리 4바이트가 들어간다.
- Adler-32 가 맞지 않으면 오류다(`fatal: mygit: corrupt zlib stream`).

---

## 4. 객체

### 4.1 이름 = SHA-1(머리 + 몸)

```text
머리 = <형식> SP <몸의 바이트 수(10진)> NUL
이름 = SHA-1(머리 ‖ 몸)
```

형식은 `blob`·`tree`·`commit`·`tag` 넷이다. 크기는 앞에 0 을 붙이지 않은
10진 ASCII. 머리의 NUL 뒤가 곧 몸이다. 빈 blob 과 빈 트리의 이름은 이렇다:

<!--EX empty-->
```text
$ git hash-object -t blob /dev/null
e69de29bb2d1d6434b8b29ae775ad8c2e48c5391
$ git hash-object -t tree /dev/null
4b825dc642cb6eb9a060e54bf8d69288fbee4904
```
<!--/EX-->

### 4.2 blob

몸 = 파일 내용 그대로. 이름도 권한도 들어 있지 않다(그것은 트리의 몫이다).

<!--EX blob-->
```text
$ printf 'hello\n' | git hash-object -w --stdin
ce013625030ba8dba906f756967f9e9ca394464a
# .git/objects/ce/013625030ba8dba906f756967f9e9ca394464a 를 zlib 으로 푼 바이트
0000  62 6c 6f 62 20 36 00 68 65 6c 6c 6f 0a           |blob 6.hello.|
```
<!--/EX-->

### 4.3 tree

몸은 항목을 이어 붙인 것이다. 항목 하나:

```text
<모드(8진 ASCII, 앞 0 없음)> SP <이름 바이트> NUL <객체 이름 20바이트(이진)>
```

| 모드 | 뜻 | mygit 작업 트리 쓰기 |
|---|---|---|
| `100644` | 보통 파일 | 한다 |
| `100755` | 실행 파일 | 한다 |
| `120000` | 심볼릭 링크(blob 몸 = 링크 대상 경로) | 안 한다(§0.2) |
| `40000` | 하위 트리 | 한다 |
| `160000` | 서브모듈(가리키는 것은 **다른 저장소의 커밋**) | 안 한다 |

트리 몸의 디렉터리 모드는 `40000` 다섯 글자이고, `cat-file -p` 와 `ls-tree` 는
그것을 `040000` 여섯 글자로 **찍어 보일 뿐**이다. 몸에 `040000` 을 쓰면 이름이
달라지고, `git fsck` 는 `zeroPaddedFilemode` 경고를, `git fsck --strict` 는
같은 이름의 오류를 낸다(2026-09-18 확인). 부록 A 의 모든 검사는 `--strict` 다.

<!--EX tree-->
```text
$ git cat-file -p 0483cb5f99e3fa107c768c654b40b1cf1999f914
100644 blob ce013625030ba8dba906f756967f9e9ca394464a	hello.txt
100755 blob 4163036efa65bd4a469e752267498f01ea36a55c	run.sh
040000 tree ffe6262bce1d713489e34cf6f2995e58168f005a	src
# 트리 0483cb5 를 푼 바이트 (id 는 20바이트 이진)
0000  74 72 65 65 20 31 30 31 00 31 30 30 36 34 34 20  |tree 101.100644 |
0010  68 65 6c 6c 6f 2e 74 78 74 00 ce 01 36 25 03 0b  |hello.txt...6%..|
0020  a8 db a9 06 f7 56 96 7f 9e 9c a3 94 46 4a 31 30  |.....V......FJ10|
0030  30 37 35 35 20 72 75 6e 2e 73 68 00 41 63 03 6e  |0755 run.sh.Ac.n|
0040  fa 65 bd 4a 46 9e 75 22 67 49 8f 01 ea 36 a5 5c  |.e.JF.u"gI...6.\|
0050  34 30 30 30 30 20 73 72 63 00 ff e6 26 2b ce 1d  |40000 src...&+..|
0060  71 34 89 e3 4c f6 f2 99 5e 58 16 8f 00 5a        |q4..L...^X...Z|
```
<!--/EX-->

**정렬 규칙 — 트리 안의 항목 차례.** 항목은 이름의 바이트로 정렬하되,
**하위 트리의 이름은 뒤에 `/` 가 붙은 것처럼** 비교한다. 파일 `a-b`
(`-` = 0x2d)와 `a.b`(0x2e)는 디렉터리 `a`(`a/`, 0x2f)보다 앞이고, `a=b`
(0x3d)·`ab` 는 뒤다. 이름만으로 정렬하면 `a` 가 맨 앞으로 와서 이름이
다른 트리가 된다 — 3부와 부록 A 4단계가 이 함정을 캡처로 보인다.

인덱스(§7)는 **전체 경로**를 바이트로 정렬한다. 전체 경로 `a/x` 는 이미
`/` 를 품고 있으므로, 인덱스 차례와 "트리를 재귀로 펼친 차례" 는 언제나
같다 — 트리의 규칙은 바로 그것을 맞추려고 있다.

<!--EX tree-sort-->
```text
$ git ls-files --stage
100644 7f07527a80bd8c2b1c5087d7ccfe61073b068374 0	a-b
100644 4e1c325aa34092ee6605530a43543d2f371db5b1 0	a.b
100644 d4f4cb2022df7646e1500f1c5b8827dcd9353722 0	a/x
100644 efc73add7dd868242a66faf2a59b145f2a60b834 0	a=b
100644 81bf396956110ad81c14860af1bbcc9dfbe4df20 0	ab
$ git ls-tree 461acf76af5f7a0d38a05d2f1fc17482af8935e3
100644 blob 7f07527a80bd8c2b1c5087d7ccfe61073b068374	a-b
100644 blob 4e1c325aa34092ee6605530a43543d2f371db5b1	a.b
040000 tree 34c2d24ff4bd6c52f81983e24f62425c4b3e07d6	a
100644 blob efc73add7dd868242a66faf2a59b145f2a60b834	a=b
100644 blob 81bf396956110ad81c14860af1bbcc9dfbe4df20	ab
```
<!--/EX-->

### 4.4 commit

```text
tree <트리 이름 40글자>
parent <부모 이름 40글자>        (부모 수만큼, 0개 이상, 주어진 차례대로)
author <이름> <<메일>> <초> <±hhmm>
committer <이름> <<메일>> <초> <±hhmm>
                                 (빈 줄 하나)
<메시지>
```

- 머리 줄은 이 차례 그대로다. mygit 은 `encoding`·`gpgsig`·`mergetag` 머리를
  쓰지 않는다. 읽을 때는 모르는 머리 줄(이어지는 줄은 공백으로 시작한다)을
  건너뛴다.
- 신원 줄의 꼴: `이름 SP < 메일 > SP 초 SP 시간대`. 시간대는 `+0900` 처럼
  부호와 네 자리. 이름과 메일은 환경 변수 그대로(§1.3).
- 메시지 규칙은 명령마다 다르다(진짜 git 에서 확인, `golden/scen/plumbing.scn`).

| 어떻게 만들었나 | 몸의 메시지 |
|---|---|
| `commit-tree -m <m>` | `<m>` 그대로 + `\n`. 앞뒤 공백도 그대로 남는다 |
| `commit-tree -m <m1> -m <m2>` | `<m1>\n\n<m2>\n` |
| `commit -m <m>` | **공백 정리** 뒤 + `\n`: 줄마다 끝 공백을 지우고, 앞뒤의 빈 줄을 지우고, 이어진 빈 줄은 하나로 줄인다. 줄 앞의 공백은 남긴다 |
| `commit -m <m1> -m <m2>` | `<m1>\n\n<m2>` 를 만든 뒤 공백 정리 |

예: `commit -m "\n\n  lead  \n\nx   \n \n\n\ny\n\n"` 의 메시지는
`  lead\n\nx\n\ny\n` 이 된다.

**제목(subject)** 은 메시지의 **첫 문단**(첫 빈 줄 앞까지)의 줄들을 공백
하나로 이은 것이다. 줄 끝의 공백은 떼고 **줄 앞의 공백은 남긴다** — 메시지
`  lead\n…` 의 제목은 `  lead` 다(`golden/scen/plumbing.scn`, 진짜 git 확인). `log --oneline`, `commit` 의 요약 줄, reflog 의 한 줄이
모두 제목을 쓴다. 메시지가 `second\nbody line\n\npara2\n` 이면 제목은
`second body line` 이다.

<!--EX commit-->
```text
$ git cat-file -p HEAD
tree 1db173a96b4a0939c490b0583539e6ccb945cc5b
parent fd4693d38f3820eb9fb7c198837629bab923893f
author A U Thor <author@example.com> 1700000000 +0900
committer C O Mitter <committer@example.com> 1700000000 +0900

second

body line
# 헤더: 'commit 229\x00'
$ git log --oneline
f20679c second
fd4693d first
```
<!--/EX-->

### 4.5 tag (주석 태그)

```text
object <가리키는 객체 이름>
type <그 객체의 형식>
tag <태그 이름>
tagger <커미터 신원 줄>
                                 (빈 줄)
<메시지 — commit -m 과 같은 공백 정리 + \n>
```

가벼운 태그는 객체가 아니다 — `refs/tags/<이름>` 파일 하나다(§6).

<!--EX tag-->
```text
$ git cat-file -p v1.0
object fd4693d38f3820eb9fb7c198837629bab923893f
type commit
tag v1.0
tagger C O Mitter <committer@example.com> 1700000000 +0900

release 1.0
```
<!--/EX-->

### 4.6 객체 API (다섯 언어 공통, 이름은 §15)

- `hashObject(type, body) → 이름` — 머리를 붙여 SHA-1.
- `writeObject(repo, type, body) → 이름` — 이미 있으면 아무것도 안 한다.
  없으면 `objects/xx/` 를 만들고 임시 파일에 쓴 뒤 이름을 바꿔 넣는다
  (중간에 죽어도 반쯤 쓴 객체가 남지 않게). 권한은 0444(git 과 같다).
- `readObject(repo, 이름) → (형식, 몸)` — 느슨한 객체를 먼저, 없으면 팩(§13)을
  찾는다. 풀어 본 머리의 크기와 몸의 길이가 다르면 오류.
- 이름 앞부분(4글자 이상)으로 찾기: 느슨한 객체 디렉터리와 팩 색인을 모두
  훑어 하나만 맞으면 그것, 여럿이면 "모호함", 없으면 "없음".

---

## 5. 저장소 배치

### 5.1 `init` 이 만드는 것

```text
.git/HEAD            "ref: refs/heads/main\n"
.git/config          아래 네 줄짜리 설정
.git/objects/        (비어 있음)
.git/objects/pack/   (비어 있음)
.git/refs/heads/     (비어 있음)
.git/refs/tags/      (비어 있음)
```

`config` 의 내용은 `git init` 이 쓰는 것과 바이트까지 같다(탭 들여쓰기):

```text
[core]
	repositoryformatversion = 0
	filemode = true
	bare = false
	logallrefupdates = true
```

git 은 이 밖에 `description`·`hooks/`(견본 스크립트)·`info/exclude` 를 만든다.
mygit 은 만들지 않는다 — 없어도 git 이 그 저장소를 여는 데 아무 문제가 없다
(`git fsck --strict`·`git status` 로 확인한다). 표준 출력:
`Initialized empty Git repository in <절대 경로>/.git/`. 이미 저장소면
`Reinitialized existing Git repository in <절대 경로>/.git/` 를 쓰고 아무것도
덮어쓰지 않는다. 기본 브랜치 이름은 언제나 `main` 이다(`-b` 없음).

### 5.2 느슨한 객체와 팩

- 느슨한 객체: `.git/objects/<이름 앞 2글자>/<나머지 38글자>`, 내용은 §3 의 zlib.
- 팩: `.git/objects/pack/pack-<체크섬>.pack` 과 같은 이름의 `.idx`.
  `<체크섬>` 은 `.pack` 파일 끝 20바이트(팩 전체의 SHA-1)의 16진이다.
  같은 디렉터리의 `.rev`·`.mtimes`·`.keep`·`.promisor` 는 git 2.55 가 만들
  수 있지만 mygit 은 읽지 않고 쓰지도 않는다.
- 찾는 차례: 느슨한 객체 → 팩(파일 이름의 바이트 차례). 같은 객체가 두 곳에
  있으면 먼저 찾은 것을 쓴다(내용이 같으므로 어느 쪽이든 같다).

---

## 6. 참조

### 6.1 파일

| 파일 | 내용 |
|---|---|
| `.git/refs/heads/<브랜치>` | `<40글자>\n` |
| `.git/refs/tags/<태그>` | `<40글자>\n` (주석 태그면 태그 객체의 이름) |
| `.git/refs/remotes/<원격>/<브랜치>` | `<40글자>\n` |
| `.git/HEAD` | `ref: refs/heads/<브랜치>\n` 또는 분리 상태에서 `<40글자>\n` |
| `.git/ORIG_HEAD` · `MERGE_HEAD` | `<40글자>\n` (merge 가 쓴다, §12) |
| `.git/packed-refs` | 아래 |

`packed-refs` 는 읽기만 한다(git 이 `gc`·`pack-refs` 로 만든 저장소를 clone·
fetch 할 때 필요하다). 꼴:

```text
# pack-refs with: peeled fully-peeled sorted␠
<40글자> SP <참조 이름>
^<40글자>                        (바로 윗줄 주석 태그가 가리키는 객체, 있을 때만)
```

(`␠` 는 공백 한 칸 — git 2.55 는 첫 줄 끝에 공백을 남긴다. 2026-09-18 확인.)
`#` 줄은 건너뛴다. 느슨한 파일과 `packed-refs` 에 같은 이름이 있으면
**느슨한 파일이 이긴다**. 참조를 고치거나 지울 때는 느슨한 파일만 만지고,
`packed-refs` 에만 있는 참조를 지우는 일은 줄임이다(오류로 끝낸다).

참조 파일은 `<이름>.lock` 에 쓴 뒤 이름을 바꿔 넣는다. `.lock` 이 이미
있으면 `fatal: mygit: unable to lock <이름>` 으로 끝낸다.

### 6.2 이름 풀기 (`<rev>`)

차례대로 해 보고 처음 맞는 것을 쓴다(git 의 rev-parse 규칙에서 mygit 이
쓰는 부분).

1. 40글자 16진 → 그 객체(있는지 확인한다).
2. `HEAD`·`ORIG_HEAD`·`MERGE_HEAD` → `.git/` 의 그 파일.
3. `refs/…` 로 시작 → 그 참조.
4. `refs/tags/<x>` → `refs/heads/<x>` → `refs/remotes/<x>` →
   `refs/remotes/<x>/HEAD` 차례로 있는 것.
5. 4~39글자 16진 → 앞부분이 맞는 객체가 하나뿐일 때 그것.

뒤붙이(여러 번 이어 붙일 수 있다):

| 뒤붙이 | 뜻 |
|---|---|
| `~<n>` (`~` 는 `~1`) | 첫 부모를 n 번 |
| `^<n>` (`^` 는 `^1`) | n 번째 부모. `^0` 은 자기 자신(태그면 벗긴 커밋) |
| `^{tree}` · `^{commit}` | 태그를 벗기고, 커밋이면 그 트리 |

주석 태그가 커밋 자리에 오면 벗겨서 커밋으로 쓴다(`log v1.0` 처럼).

### 6.3 reflog

`core.logAllRefUpdates=true`(§5.1 의 설정)이므로 브랜치와 HEAD 가 움직일
때마다 한 줄씩 붙인다. 파일은 `.git/logs/HEAD` 와 `.git/logs/refs/heads/<브랜치>`.

```text
<옛 40글자> SP <새 40글자> SP <커미터 이름> SP <<메일>> SP <초> SP <시간대> TAB <메시지> LF
```

처음 생긴 참조의 옛 값은 `0` 40개. 메시지는 git 과 같게 쓴다(진짜 git 에서 확인):

| 일 | HEAD 로그 | 브랜치 로그 |
|---|---|---|
| 첫 커밋 | `commit (initial): <제목>` | 같음 |
| 커밋 | `commit: <제목>` | 같음 |
| 머지 커밋(§12) | `commit (merge): <제목>` | 같음 |
| `branch <b> [<start>]` | — | `branch: Created from <start 를 준 그대로, 없으면 HEAD>` |
| `switch -c <b>` | `checkout: moving from <옛> to <b>` | `branch: Created from HEAD` |
| `switch <b>` · `checkout <x>` | `checkout: moving from <옛> to <x 를 준 그대로>` — 이미 그 브랜치여도(`Already on`) 한 줄 남긴다 | — |
| fast-forward 머지 | `merge <b>: Fast-forward` | 같음 |
| `clone` | `clone: from <원본 경로>` | 같음 |

`<옛>` 은 떠나는 브랜치 이름, 분리 상태에서 떠날 때는 **40글자 이름**이다
(진짜 git 이 그렇게 쓴다: `checkout: moving from 9933975…(40글자) to main`).
`reflog [<ref>]` 는 새것부터 `<7글자> <ref>@{<n>}: <메시지>` 로 찍는다
(`<ref>` 를 안 주면 `HEAD`).

---

## 7. 인덱스 (`.git/index`, 판 2)

### 7.1 전체 배치 — 수는 전부 빅 엔디언

| 자리 | 크기 | 내용 |
|---|---|---|
| 0 | 4 | `DIRC` |
| 4 | 4 | 판 = 2 (읽을 때는 3 도 받는다, 4 는 `fatal: mygit: index v4 unsupported`) |
| 8 | 4 | 항목 수 |
| 12 | … | 항목들(§7.2), 경로 바이트 차례, 같은 경로면 단계(stage) 차례 |
| … | … | 확장(쓰지 않는다, 읽을 때 건너뛴다 — §7.5) |
| 끝−20 | 20 | 앞의 모든 바이트의 SHA-1 |

### 7.2 항목 하나

| 자리 | 크기 | 칸 | mygit 이 쓰는 값 |
|---|---|---|---|
| 0 | 4+4 | ctime 초·나노초 | 파일의 stat |
| 8 | 4+4 | mtime 초·나노초 | 파일의 stat |
| 16 | 4 | dev | 파일의 stat (32비트로 자름) |
| 20 | 4 | ino | 파일의 stat (32비트로 자름) |
| 24 | 4 | mode | `0x81a4`(100644) 또는 `0x81ed`(100755) |
| 28 | 4 | uid | 파일의 stat |
| 32 | 4 | gid | 파일의 stat |
| 36 | 4 | size | 파일 크기 (32비트로 자름) |
| 40 | 20 | 객체 이름 | blob 이름 |
| 60 | 2 | flags | 아래 |
| 62 | n | 경로 | UTF-8 바이트, NUL 없음 |
| 62+n | 1‥8 | NUL 채움 | 항목 길이가 8의 배수가 되도록, **적어도 1** |

- flags: 비트 15 assume-valid(쓰지 않음 = 0), 비트 14 extended(판 2 에서 0),
  비트 13‥12 단계(0 = 보통, 1 = 공통 조상, 2 = 우리, 3 = 그들 — §12),
  비트 11‥0 경로 길이(0xFFF 이상이면 0xFFF).
- 항목 길이 = `(62 + n + 8) & ~7` — 경로 뒤 NUL 이 1~8개 붙는다.
- 모드의 실행 비트: stat 의 소유자 실행 비트(0o100)가 서 있으면 100755(git 과 같다).
- **stat 칸을 채우는 까닭** — git 은 이 칸으로 "파일이 안 바뀌었다" 를 해시 없이
  판단한다(stat 캐시, 5부). mygit 이 채워 두면 진짜 git 이 mygit 의 인덱스를
  열었을 때 파일을 다시 해시하지 않는다.
- **mygit 자신은 stat 캐시를 믿지 않는다** — `status`·`diff` 는 언제나 작업
  트리 파일을 해시해 비교한다. 느리지만 racy git(같은 초 안에 고친 파일을
  놓치는 문제, 5부)이 원천적으로 없다. 줄임이자 선택이다.

### 7.3 다섯 구현과 git 을 견주는 법

stat 칸은 기계·시각마다 다르다. 그래서 인덱스를 견줄 때는 **항목마다
0‥23 과 28‥35 바이트(ctime·mtime·dev·ino·uid·gid)를 0 으로 지우고 끝 SHA-1 을
다시 계산한 것**을 비교한다. mode·size·이름·flags·경로·채움은 그대로 비교한다.
아래는 진짜 git 이 쓴 인덱스를 그렇게 지운 것이다 — mygit 의 인덱스를 같은
방식으로 지우면 바이트까지 같아야 한다.

<!--EX index-->
```text
$ git ls-files --stage
100644 ce013625030ba8dba906f756967f9e9ca394464a 0	hello.txt
100755 4163036efa65bd4a469e752267498f01ea36a55c 0	run.sh
100644 b917a726c93f902e43291d9009d6488385133b67 0	src/a.py
# .git/index — stat 칸을 0 으로 지우고 끝 SHA-1 을 다시 계산
0000  44 49 52 43 00 00 00 02 00 00 00 03 00 00 00 00  |DIRC............|
0010  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00  |................|
0020  00 00 00 00 00 00 81 a4 00 00 00 00 00 00 00 00  |................|
0030  00 00 00 06 ce 01 36 25 03 0b a8 db a9 06 f7 56  |......6%.......V|
0040  96 7f 9e 9c a3 94 46 4a 00 09 68 65 6c 6c 6f 2e  |......FJ..hello.|
0050  74 78 74 00 00 00 00 00 00 00 00 00 00 00 00 00  |txt.............|
0060  00 00 00 00 00 00 00 00 00 00 00 00 00 00 81 ed  |................|
0070  00 00 00 00 00 00 00 00 00 00 00 12 41 63 03 6e  |............Ac.n|
0080  fa 65 bd 4a 46 9e 75 22 67 49 8f 01 ea 36 a5 5c  |.e.JF.u"gI...6.\|
0090  00 06 72 75 6e 2e 73 68 00 00 00 00 00 00 00 00  |..run.sh........|
00a0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00  |................|
00b0  00 00 00 00 00 00 81 a4 00 00 00 00 00 00 00 00  |................|
00c0  00 00 00 09 b9 17 a7 26 c9 3f 90 2e 43 29 1d 90  |.......&.?..C)..|
00d0  09 d6 48 83 85 13 3b 67 00 08 73 72 63 2f 61 2e  |..H...;g..src/a.|
00e0  70 79 00 00 51 1e c6 21 4e 33 63 ea 66 8b 6d ce  |py..Q..!N3c.f.m.|
00f0  3f ce b0 aa fc 2a 6a 07                          |?....*j.|
```
<!--/EX-->

### 7.4 쓰기

항목 전체를 차례대로 쓰고 끝에 SHA-1 을 붙인다. `index.lock` 에 쓴 뒤 이름을
바꿔 넣는다. 확장은 쓰지 않는다 — git 이 커밋할 때 붙이는 `TREE`(캐시 트리)
확장이 없어도 git 은 인덱스를 읽고, 필요하면 스스로 다시 만든다.

### 7.5 읽기

항목을 다 읽은 뒤 끝 20바이트 앞까지 남은 것은 확장이다. 확장 하나는
`<서명 4바이트><길이 4바이트><몸>` 이고 mygit 은 몸을 건너뛴다. 끝 SHA-1 이
맞지 않으면 `fatal: mygit: index file corrupt`.

---

## 8. 작업 트리와 `status`

### 8.1 훑기

작업 트리 뿌리에서 디렉터리를 재귀로 훑는다. 한 디렉터리 안의 항목은 이름
바이트 차례로 본다. `.git` 은 건너뛴다(§1.5). 보통 파일만 파일로 친다 —
심볼릭 링크·장치 파일은 없는 것으로 본다(§0.2). 빈 디렉터리는 아무것도 아니다.

### 8.2 경로 따옴표 (git 의 core.quotePath=true)

사람에게 경로를 찍는 자리(`status`·`cat-file -p` 의 트리·`diff` 머리)에서, 경로에 아래 바이트가 하나라도 있으면 경로 전체를 `"` 로
감싸고 C 식으로 이스케이프한다. 없으면 그대로 찍는다.

**공백 하나의 예외** — `status` 만은 경로에 공백(0x20)이 있어도 따옴표로 감싼다
(공백 자체는 이스케이프하지 않는다: `?? "sp ace"`). `cat-file -p`·
`diff` 머리·`stage` 는 공백만으로는 감싸지 않는다(진짜 git 으로 확인 —
`golden/scen/status.scn`). git 의 porcelain 출력이 기계가 읽기 쉽게 한 선택이다.

**`rm --cached` 는 감싸지 않는다** — `rm '<경로>'` 의 경로는 탭·한글이 있어도
날것 그대로다(진짜 git 2.55 로 확인, 2026-09-18).

| 바이트 | 찍는 꼴 |
|---|---|
| `\a \b \t \n \v \f \r` (0x07‥0x0d) | 그 두 글자 |
| `"` · `\` | `\"` · `\\` |
| 그 밖의 0x00‥0x1f, 0x7f, 0x80‥0xff | `\ooo` (3자리 8진) |

그래서 `한글.txt` 는 `"\355\225\234\352\270\200.txt"` 로 찍힌다(UTF-8 여섯
바이트). `diff` 머리에서는 `a/`·`b/` 까지 따옴표 안에 들어간다:
`diff --git "a/\355….txt" "b/\355….txt"`. 14부가 NFC/NFD 이야기를 이 꼴로 한다.

### 8.3 `status` — `git status --porcelain` 과 바이트까지 같다

한 줄에 경로 하나: `XY SP 경로`.

| 칸 | 견주는 것 | 글자 |
|---|---|---|
| X | HEAD 트리 ↔ 인덱스(단계 0) | `A` 새로 · `M` 내용이나 모드가 다름 · `D` 인덱스에 없음 · 공백 같음 |
| Y | 인덱스 ↔ 작업 트리 | `M` 해시나 실행 비트가 다름 · `D` 파일이 없음 · 공백 같음 |

- 충돌 중인 경로(단계 1‥3 이 있는 경로)는 `UU`(양쪽 수정), `AA`(양쪽 추가).
  그 밖의 충돌 꼴은 mygit 이 만들지 않는다(§12).
- 추적하지 않는 파일은 `?? 경로`. 줄 차례는 **추적 중인 것 전부(경로 차례)
  → 추적하지 않는 것 전부(경로 차례)**.
- **추적하지 않는 디렉터리는 접는다** — 인덱스에 그 디렉터리 아래 경로가
  하나도 없고, 그 안(재귀)에 파일이 하나라도 있으면 `?? d/` 한 줄로 찍고
  안으로 들어가지 않는다. 인덱스에 아래 경로가 있는 디렉터리는 들어가서
  같은 규칙을 적용한다. git 의 기본값(status.showUntrackedFiles=normal)과 같다.
- 바뀐 것이 없으면 아무것도 찍지 않는다. 종료 코드는 언제나 0.
- HEAD 가 아직 없는 저장소(첫 커밋 전)에서는 HEAD 트리를 빈 트리로 본다.
- Y 를 가리기 위해 작업 트리 파일을 **언제나 해시한다**(§7.2).

---

## 9. 명령마다의 출력

아래 "출력" 칸은 **git 과 바이트까지 같아야 하는 것**이다. "줄임" 칸은
mygit 이 git 보다 덜 찍는 것이고, 거기서는 mygit 의 출력이 git 과 다르다.

| 명령 | 표준 출력 | 표준 오류 | 줄임 |
|---|---|---|---|
| `init` | `Initialized empty Git repository in <절대>/.git/` | — | §5.1 |
| `hash-object` | `<40글자>` | — | `-t` 는 `blob`·`tree`·`commit`·`tag` 만, 내용 검사 없음 |
| `cat-file -t`·`-s` | 형식 · 몸의 바이트 수 | — | |
| `cat-file -p` | blob·commit·tag 는 몸 그대로, tree 는 항목마다 `%06o SP 형식 SP 40글자 TAB 경로(§8.2)` | — | |
| `add` | (없음) | — | pathspec 은 파일·디렉터리·`.` 만(와일드카드 없음) |
| `rm --cached` | 경로마다 `rm '<경로>'` (인덱스 차례) | — | 디렉터리는 받지 않는다(`-r` 없음) |
| `status` | §8.3 | — | |
| `write-tree`·`commit-tree` | `<40글자>` | — | |
| `commit` | `[<브랜치> (root-commit) <7글자>] <제목>` — 부모가 있으면 `(root-commit) ` 없이, 분리 상태면 `<브랜치>` 자리에 `detached HEAD` | — | git 이 이어 찍는 ` Author:` 줄·변경 통계·`create mode` 줄 |
| `log` | §9.1 | — | |
| `branch` | §9.2 | — | |
| `switch`·`checkout` | (없음) | §9.3 | |
| `tag` | 목록이면 이름 차례로 한 줄씩, 만들 때는 없음 | — | |
| `reflog` | §6.3 | — | |
| `diff` | §11 | — | |
| `merge` | §12 | — | 변경 통계 |

`add` 는 pathspec 아래에서 **사라진 파일을 인덱스에서 뺀다**(git 2.x 의
`add .` 과 같다). 바뀌지 않은 파일은 stat 칸만 새로 채운다. 아무 파일에도
맞지 않는 pathspec 은 §1.4 의 오류다.

`commit` 은 인덱스의 트리가 HEAD 의 트리와 같고 `MERGE_HEAD` 도 없으면
`nothing to commit` 을 표준 출력에 쓰고 1 로 끝난다(git 은 여기서 `status`
전체를 찍는다 — 줄임). 충돌 경로가 남아 있으면 표준 오류에 아래 두 줄을
쓰고 128 로 끝난다(git 은 그 뒤에 충돌 경로 목록을 더 찍는다 — 줄임).

```text
error: Committing is not possible because you have unmerged files.
fatal: Exiting because of an unresolved conflict.
```

### 9.1 `log`

기본 꼴 — 커밋마다(둘째 커밋부터는 앞에 빈 줄 하나):

```text
commit <40글자>
Merge: <첫 부모 7글자> <둘째 부모 7글자>      (부모가 둘 이상일 때만, 부모 차례대로)
Author: <이름> <<메일>>
Date:   <작성 날짜>
                                               (빈 줄)
    <메시지 첫 줄>
    <메시지의 줄마다 네 칸 들여쓰기, 빈 줄은 "    " 네 칸만>
```

- 날짜는 **author** 의 시각을 **author 의 시간대로** 옮겨
  `<요일> <달> <일> <시>:<분>:<초> <해> <±hhmm>` 으로 찍는다. 요일·달은 영어
  세 글자(`Mon`…, `Jan`…), 일은 앞에 0 을 붙이지 않고, 시·분·초는 두 자리.
  예: `1700000000 +0900` → `Wed Nov 15 07:13:20 2023 +0900`.
  달력 계산은 그레고리력 날짜 공식(days-from-civil)으로 하고 언어의 로캘
  날짜 함수를 쓰지 않는다.
- 메시지 끝의 `\n` 하나는 줄로 치지 않는다.
- `--oneline`: `<7글자> SP <제목(§4.4)>`. 장식(`(HEAD -> main)`)은 찍지 않는다 —
  git 도 출력이 단말이 아니면 찍지 않는다.
- `-n <N>`: 처음 N 개만. 차례는 §10.

### 9.2 `branch`

- 목록: `refs/heads/` 아래 이름을 바이트 차례로, 지금 브랜치 앞에 `* `,
  나머지 앞에 두 칸. 분리 상태면 맨 앞에 `* (HEAD detached at <7글자>)` 를
  한 줄 더 찍는다. (git 은 분리할 때 쓴 이름으로 `at v1.0` 처럼 찍기도 한다 —
  mygit 은 언제나 7글자다. 줄임.)
- 만들기 `branch <b> [<start>]`: 조용히. 이미 있으면
  `fatal: a branch named '<b>' already exists` (128). 이름 규칙에 어긋나면
  `fatal: '<b>' is not a valid branch name` (128) — 규칙은 `..`·공백·`~^:?*[\`·
  제어 문자를 품지 않고, `-`·`.`·`/` 로 시작하지 않고, `/`·`.`·`.lock` 으로
  끝나지 않고, `@{` 를 품지 않고, `@` 하나가 아닐 것.
- 지우기 `branch -d <b>`: HEAD 에서 닿는 커밋이면 `Deleted branch <b> (was <7글자>).`
  (표준 출력) · 아니면 `error: the branch '<b>' is not fully merged` (1). 지금
  브랜치는 지우지 않는다 — `error: cannot delete branch '<b>' used by worktree at '<절대 경로>'` (1).

### 9.3 `switch`·`checkout`

| 경우 | 표준 오류 |
|---|---|
| 다른 브랜치로 | `Switched to branch '<b>'` |
| `switch -c <b>` | `Switched to a new branch '<b>'` (첫 커밋 전이면 HEAD 가 가리키는 이름만 바꾼다) |
| 이미 그 브랜치 | `Already on '<b>'` |
| `checkout <커밋>` (분리) | `HEAD is now at <7글자> <제목>` |
| 분리 상태에서 떠날 때 | 위 줄 앞에 `Previous HEAD position was <7글자> <제목>` — **새 커밋이 옛 커밋과 다를 때만**(같으면 git 도 찍지 않는다, `golden/scen/checkout.scn`) |
| `switch <커밋>` | `fatal: a branch is expected, got commit '<x>'` (128) |

**남은 변경 알림** — 바꾸기에 성공하면(`Already on` 포함) 새 HEAD 트리와 견주어
작업 트리나 인덱스가 다른 추적 경로를 경로 차례로 표준 출력에 찍는다
(단 `switch -c` 가 **지금 커밋에서** 새 브랜치를 만들 때는 찍지 않는다 — git 이
그때는 작업 트리를 아예 건드리지 않는다):
`<글자> TAB <경로(§8.2)>`. 글자는 `M`(내용·모드가 다름) · `D`(작업 트리에 없음) ·
`A`(인덱스에만 있고 새 HEAD 에 없음). 규칙 1 로 따라온 손댄 파일이 여기 나온다
(진짜 git 으로 확인, `golden/scen/checkout.scn`).

git 은 분리할 때 안내 문단(advice)을 더 찍지만 `GIT_ADVICE=0`(tools/gitenv.sh)
이면 찍지 않는다. mygit 은 안내를 찍지 않으므로 그 환경의 git 과 같다.

**바꾸는 규칙** (git 의 두 갈래 합치기, twoway merge 와 같다). 옛 트리 O(지금 HEAD),
새 트리 N, 인덱스 I, 작업 트리 W 에 대해 경로마다:

1. O 와 N 에서 같다 → 인덱스·작업 트리를 **그대로 둔다**(손댄 내용이 따라온다).
2. 다르다 → I 가 O 와 같고(없으면 없음끼리) W 가 I 와 같아야 한다. 아니면 충돌.
3. O 에 없고 N 에 있는데 추적하지 않는 파일이 W 에 있다 → 충돌.

충돌이 하나라도 있으면 아무것도 바꾸지 않고 코드 1 로 끝낸다. 표준 오류
(`GIT_ADVICE=0` 의 git 과 같다 — 안내 문장 자리가 **빈 줄**로 남는다):

```text
error: Your local changes to the following files would be overwritten by checkout:
	<경로>                                   (탭 하나 + 경로, 경로 차례)

Aborting
```

3 의 경우는 첫 줄만 `error: The following untracked working tree files would be
overwritten by checkout:` 로 바뀐다. 둘이 섞이면 1·2 의 묶음을 먼저 찍는다.
충돌이 없으면 N 에 없어진 경로를 지우고(비게 된
디렉터리도 지운다), 달라진 경로를 쓰고, 인덱스 항목을 새 stat 으로 채운다.
파일은 0666, 실행 파일은 0777 로 만들고 umask 를 따른다.

---

## 10. 역사 걷기와 merge-base

### 10.1 `log` 의 차례 — 날짜 줄, 같은 날짜는 먼저 온 것이 먼저

git 의 기본 `log`(옵션 없음)와 같은 차례를 이렇게 만든다. **커미터 날짜**
(`committer` 줄의 초)를 쓴다.

```text
큐 ← [시작 커밋]                  날짜 내림차순으로 늘 정렬된 목록
본 것 ← {시작 커밋}
큐가 빌 때까지:
    c ← 큐의 맨 앞을 꺼낸다 → 찍는다
    c 의 부모 p 마다 (커밋에 적힌 차례대로):
        p 가 본 것에 없으면: 본 것에 넣고, 큐에 날짜 차례로 끼운다 —
        **날짜가 같은 것들 중에서는 맨 뒤에** (먼저 들어온 것이 먼저 나간다)
```

git 의 `commit_list_insert_by_date` 가 바로 이 끼우기다. `tools/gitenv.sh` 는
모든 커밋의 날짜를 같게 만드므로, 이 덱의 저장소에서는 **같은 날짜 규칙이
차례의 전부**가 된다. 진짜 git 으로 확인한 예(2026-09-18): A←B, B 에서 갈라진
`C D` 와 `E F`, 머지 M1(D, F), `G`(main)·`H`(t), 머지 M2(G, H), I — 모든 날짜가
같을 때 `git log` 의 차례는 `I M2 G H M1 F D E C B A` 이고 위 규칙이 같은 답을
낸다. `golden/dag/` 가 이 역사와 날짜가 모두 다른 역사를 둘 다 갖는다.

### 10.2 `merge-base`

- 공통 조상 = a 의 조상(자기 포함)이면서 b 의 조상인 커밋.
- **가장 좋은** 공통 조상 = 다른 공통 조상의 조상이 **아닌** 공통 조상.
- `merge-base a b` 는 가장 좋은 것 하나, `--all` 은 전부를 한 줄에 하나씩.
- 차례: 커미터 날짜 내림차순. 가장 좋은 것이 여럿이고 날짜까지 같으면 차례는
  이 문서가 정하지 않는다 — `golden/dag/` 의 criss-cross 역사는 그래서 날짜를
  모두 다르게 만든다. 셋 이상의 인자·`--octopus`·`--is-ancestor` 는 줄임.
- 없으면 아무것도 찍지 않고 1 로 끝난다(git 과 같다).

`merge`(§12)는 가장 좋은 공통 조상이 둘 이상이면 멈춘다 — git 의 ort 는
그 둘을 먼저 합쳐 가상의 조상을 만들지만 mygit 은 그러지 않는다. 줄임.

---

## 11. diff

### 11.1 줄

내용을 `\n` 으로 자른다. 각 줄은 `\n` 까지 포함한다. 마지막 줄에 `\n` 이 없으면
"끝 줄바꿈 없음" 표시가 붙은 줄이고, **표시가 다르면 다른 줄**이다(`a` 와 `a\n`
은 다르다). 두 줄의 비교는 바이트 비교다. 공백 무시 옵션은 없다.

### 11.2 편집 스크립트 — 계약

**다섯 언어가 똑같이 이 세 단계를 밟는다.** 다섯의 출력은 모든 입력에서
바이트까지 같아야 한다(`make parity`).

1. **앞뒤 깎기** — 앞에서부터 같은 줄, 그다음 뒤에서부터 같은 줄을 떼어
   바뀌지 않은 것으로 둔다(git 의 `xdl_trim_ends` 와 같다).
2. **Myers 앞방향 탐욕 탐색**(Myers 1986, 그림 2) — 남은 가운데 A[0‥N), B[0‥M)
   에서 d = 0, 1, 2, … 마다 대각선 k = −d, −d+2, …, d 를 차례로:

   ```text
   아래로(B 의 줄 끼움):  k = −d  또는  (k ≠ d 이고 V[k−1] < V[k+1])  →  x = V[k+1]
   오른쪽(A 의 줄 지움): 그 밖                                      →  x = V[k−1] + 1
   y = x − k;  A[x] = B[y] 인 동안 x, y 를 함께 늘린다;  V[k] = x
   x ≥ N 이고 y ≥ M 이면 끝
   ```

   V 는 d 마다 사본을 남겨 두고, (N, M) 에서 거꾸로 같은 판정을 되밟아
   끼운 줄·지운 줄에 표시한다. 같은 길이의 스크립트가 여럿이면 이 판정
   (`V[k−1] < V[k+1]` 일 때만 아래로)이 고른다.
3. **밀어 붙이기** (git 의 `xdl_change_compact`, 들여쓰기 휴리스틱 없이) —
   A 쪽(지운 줄, 상대는 B)과 B 쪽(끼운 줄, 상대는 A)에 차례로:

   ```text
   바뀐 줄의 묶음 g 마다 (앞에서부터):
       되풀이:
           크기 ← g 의 길이
           g 를 위로 밀 수 있는 만큼 민다     (g 바로 위 줄 = g 의 끝 줄이면 한 칸)
               — 밀 때마다 상대 파일의 묶음 표지 go 도 한 묶음 앞으로
           가장_이른_끝 ← g.end
           상대와_맞는_끝 ← (go 가 비어 있지 않으면 g.end, 아니면 없음)
           g 를 아래로 밀 수 있는 만큼 민다   (g 첫 줄 = g 바로 아래 줄이면 한 칸)
               — 밀 때마다 go 도 한 묶음 뒤로, go 가 비어 있지 않으면
                 상대와_맞는_끝 ← g.end
           밀다가 옆 묶음과 붙어 크기가 바뀌었으면 처음부터 다시
       g.end = 가장_이른_끝 이면 그대로 (움직일 수 없던 묶음)
       아니고 상대와_맞는_끝 이 있으면: go 가 빈 동안 g 를 한 칸씩 위로 되민다
       아니면 맨 아래에 둔다
   ```

   밀 때 "묶음이 옆 묶음과 붙는다" 는 것은 민 자리 바로 다음 줄도 바뀐 줄이면
   묶음을 그만큼 늘린다는 뜻이다. 한 파일의 끝에는 바뀌지 않은 가짜 줄이 하나
   있다고 치고 계산한다.

**진짜 git 과의 관계.** git 은 2 단계에서 앞방향이 아니라 **양방향(middle
snake) 분할 정복**을 쓰고, 그 전에 한쪽에만 있는 줄을 미리 걸러 낸다
(`xdl_cleanup_records`). 그래서 같은 길이의 스크립트가 여럿인 입력에서 git 은
다른 것을 고를 수 있다. 조사(2026-09-18, 무작위 1,500 쌍, `diff.indentHeuristic=false`
의 git 과 대조): 어긋난 253 쌍 가운데 252 쌍은 **지운 줄·끼운 줄의 수가 git 과
같고** 고른 줄만 달랐으며, 1 쌍은 git 쪽이 더 길었다(거르기 때문). 사람이
실제로 고친 꼴의 쌍에서는 어긋남이 드물다(2.5 %). 그래서 `golden/diff/` 는
두 목록을 갖는다.

| 목록 | 시험이 확인하는 것 |
|---|---|
| `agree.tsv` (30 쌍) | mygit 의 출력 = `git -c diff.indentHeuristic=false diff --no-index` 의 출력, 바이트까지 |
| `tie.tsv` (3 쌍) | 지운 줄·끼운 줄 수가 git 과 같고, 출력은 git 과 **다르다** — 9부가 이 차이를 보여 준다 |

코드처럼 생긴 쌍에서 tie 는 드물다 — 그런 줄 모음으로 4,000 쌍을 만들어 견주었을
때 한 쌍이 나왔다(2026-09-18). 그래서 tie 목록은 무작위 탐색에서 건진 것을
그대로 쓰고, agree 목록은 사람이 고치는 꼴로 설계했다.

들여쓰기 휴리스틱(`diff.indentHeuristic`, git 2.14 부터 기본값 켜짐)은
mygit 에 없다. 9부는 켜짐·꺼짐 두 캡처로 그 효과를 진짜 git 에서 보인다.

Python 만 2 단계의 **선형 공간 변형**(Myers 논문 4b 절의 middle snake)을 따로
갖는다(PLAN.md §9 결정 7). 그 변형의 출력은 `agree.tsv` 전부에서 앞방향의
출력과 같아야 한다 — 같은 길이의 스크립트가 여럿일 때 둘이 다를 수 있다는
것까지 그 시험의 주석이 말한다.

### 11.3 덩어리(hunk)

- 바뀐 곳(change) = 지운 줄 묶음과 끼운 줄 묶음이 같은 자리에서 만난 것. 파일
  끝에서 앞으로 훑으며 모은다(git 의 `xdl_build_script`).
- 문맥은 3 줄. 이웃한 두 바뀐 곳 사이의 바뀌지 않은 줄이 **6 줄 이하면 한
  덩어리**, 7 줄 이상이면 나눈다(진짜 git 으로 확인).
- 덩어리의 시작 s1 = max(첫 바뀐 곳의 A 자리 − 3, 0), s2 = max(첫 바뀐 곳의
  B 자리 − 3, 0) — **둘을 따로** 계산한다. 끝 e1 = min(마지막의 A 끝 + 3, N),
  e2 도 같다.
- 머리: `@@ -<a> +<b> @@` — `<a>` 는 줄 수 c 가 1 이면 `시작`, 아니면
  `시작,c`. 시작은 c > 0 이면 s+1, c = 0 이면 s(빈 쪽은 "그 줄 뒤" 를 가리킨다).
  예: 빈 파일로 → `@@ -1 +0,0 @@`, 빈 파일에서 → `@@ -0,0 +1 @@`.
- 함수 문맥: 덩어리 머리 뒤에 공백 하나와 **A 에서 s1 바로 위부터 거꾸로 찾은
  첫 "함수 줄"** 을 붙인다. 함수 줄 = 첫 바이트가 영문자·`_`·`$` 인 줄.
  줄바꿈과 끝 공백을 떼고 80 바이트에서 자르고 다시 끝 공백을 뗀다. 없으면
  아무것도 붙이지 않는다(git 기본 드라이버와 같다).
- 몸: 문맥 줄은 ` `, 지운 줄 `-`, 끼운 줄 `+`. 한 바뀐 곳 안에서는 지운 줄을
  모두 찍은 뒤 끼운 줄. 끝 줄바꿈 없는 줄 바로 다음에 `\ No newline at end of file`.

### 11.4 파일 머리

```text
diff --git a/<경로> b/<경로>             (§8.2 따옴표 — a/ b/ 까지 안에)
<모드 줄들>
index <옛 7글자>..<새 7글자>[ <모드>]
--- a/<경로>      또는  --- /dev/null
+++ b/<경로>      또는  +++ /dev/null
```

| 경우 | 모드 줄 | index 줄 |
|---|---|---|
| 내용만 바뀜 | 없음 | `index a..b 100644` |
| 새 파일 | `new file mode 100644` | `index 0000000..b` |
| 지운 파일 | `deleted file mode 100644` | `index a..0000000` |
| 모드만 바뀜 | `old mode 100644` `new mode 100755` | **없음**, `---`·`+++`·덩어리도 없음 |
| 모드와 내용이 바뀜 | 같은 두 줄 | `index a..b` (모드 없이) |

이진 파일 — 어느 쪽이든 처음 8,000 바이트 안에 NUL 이 있으면 — 은
`---`·`+++`·덩어리 대신 `Binary files a/<경로> and b/<경로> differ` 한 줄
(새 파일이면 `/dev/null and b/<경로>`).

### 11.5 무엇과 무엇을 견주나

| 명령 | 옛 쪽 | 새 쪽 | 파일 차례 |
|---|---|---|---|
| `diff` | 인덱스(단계 0) | 작업 트리 | 인덱스 차례. 추적하지 않는 파일은 없다. 충돌 경로는 건너뛴다(줄임) |
| `diff --cached` | HEAD 트리(없으면 빈 트리) | 인덱스 | 경로 차례 |
| `diff <c1> <c2>` | c1 의 트리 | c2 의 트리 | 경로 차례. **이름 변경 감지 없음** — git 은 기본으로 켜져 있으므로 비교할 git 은 `--no-renames` 로 부른다 |
| `diff --no-index <a> <b>` | 파일 a | 파일 b | 머리의 경로는 준 그대로(`a/<a> b/<b>`) |

세 경우 모두 "경로 차례" 는 전체 경로의 바이트 차례이고, 트리를 재귀로
펼친 차례와 같다(§4.3, 진짜 git 으로 확인). 종료 코드는 0 — 단
`--no-index` 는 git 과 같이 다르면 1, 같으면 0.

---

## 12. merge

### 12.1 명령의 흐름 — `merge <b>`

1. `<b>` 를 푼다(§6.2). 풀 수 없으면 §1.4 의 `merge: <b> - not something we can merge`.
2. HEAD 가 아직 태어나지 않았으면(첫 커밋 전) `fatal: mygit: nothing to merge into
   yet` (128). git 은 그 자리로 `<b>` 를 그대로 가져온다 — 줄임.
   인덱스가 HEAD 트리와 다르거나 추적 중인 파일이 작업 트리에서 바뀌었으면
   멈춘다 — `error: mygit: commit your local changes before merging` (128).
   git 은 합치기가 건드리지 않는 파일의 변경은 허락한다. 줄임.
3. `ORIG_HEAD` ← 지금 HEAD(이미 최신이어도 쓴다 — 진짜 git 과 같다,
   `golden/scen/merge-ff.scn`). `<b>` 가 HEAD 의 조상이면 `Already up to date.`
   (표준 출력, 0).
4. HEAD 가 `<b>` 의 조상이면 **fast-forward**: 표준 출력에
   `Updating <옛 7글자>..<새 7글자>` 와 `Fast-forward` 두 줄(git 은 그 뒤에 변경
   통계를 찍는다 — 줄임). `ORIG_HEAD` ← 옛 HEAD, 작업 트리·인덱스를 §9.3 의
   규칙으로 새 트리로 옮기고, 브랜치를 옮기고 reflog `merge <b>: Fast-forward`.
5. 아니면 **3-way**: 가장 좋은 공통 조상이 정확히 하나여야 한다(§10.2). 그것을
   B(base), HEAD 를 O(ours), `<b>` 를 T(theirs)로 §12.2 를 한다.

### 12.2 트리 단위 — 경로마다

세 트리를 전체 경로 → (모드, 이름) 으로 펼치고, 경로의 합집합을 경로 차례로
훑는다.

| B · O · T 의 모습 | 결과 |
|---|---|
| O = T | O |
| B = O (T 만 바뀜, 지운 것 포함) | T |
| B = T (O 만 바뀜, 지운 것 포함) | O |
| 셋 다 있고 O·T 가 다른 보통 파일 | **내용 합치기**(§12.3). 먼저 `Auto-merging <경로>` |
| B 에 없고 O·T 에 다르게 새로 생김 | B 를 빈 파일로 두고 내용 합치기. 먼저 `Auto-merging <경로>`, 충돌이면 `CONFLICT (add/add): Merge conflict in <경로>`(단계 1 없이 2·3 만) |
| 그 밖(지움 대 고침, 파일 대 디렉터리, 둘 다 모드를 다르게 바꿈) | 줄임 — `fatal: mygit: unsupported merge case (<경우>) in <경로>` (128), 아무것도 바꾸지 않는다 |

모드는 내용과 따로 같은 세 줄 규칙(O = T → O, B = O → T, B = T → O)으로 고른다.

내용 합치기가 충돌하면 `CONFLICT (content): Merge conflict in <경로>` 를 찍고,
인덱스에는 그 경로를 단계 1(B, 있을 때만)·2(O)·3(T) 세 항목으로, 작업 트리에는
충돌 표지가 든 내용을 쓴다. 충돌하지 않은 경로는 단계 0 으로 쓴다. 안내 줄은
전부 표준 출력.

**충돌이 없으면** 트리를 쓰고 커밋을 만든다 — 부모 [O, T], 작성자·커미터는
§1.3, 메시지는 `Merge branch '<b>'\n`(지금 브랜치가 `main`·`master` 가 아니면
`Merge branch '<b>' into <지금 브랜치>\n`). 같은 날짜·같은 트리라면 이 커밋의
이름은 **진짜 `git merge` 가 만든 커밋과 같아야 한다** — 부록 A 10단계의
가장 강한 시험이다. 표준 출력은 `Merge made by mygit (3-way, no renames).`
(git 은 `Merge made by the 'ort' strategy.` 와 변경 통계), reflog 는
`merge <b>: Merge made by mygit (3-way, no renames).`

**충돌이 있으면** 마지막 줄로 `Automatic merge failed; fix conflicts and then
commit the result.` 를 찍고 1 로 끝난다. `.git/` 에 쓰는 것:

| 파일 | 내용 |
|---|---|
| `MERGE_HEAD` | `<T 40글자>\n` |
| `ORIG_HEAD` | `<O 40글자>\n` |
| `MERGE_MSG` | `Merge branch '<b>'\n\n# Conflicts:\n#\t<경로>\n` (충돌 경로마다 `#\t` 한 줄, 진짜 git 과 같다) |

git 은 `MERGE_MODE`·`AUTO_MERGE` 도 쓰지만 mygit 은 쓰지 않는다. 사람이 충돌을
풀고 `add` 하면 단계 0 이 단계 1‥3 을 대신하고, `commit -m <m>` 은 부모를
[HEAD, MERGE_HEAD] 로 커밋한 뒤(reflog `commit (merge): <제목>`) `MERGE_HEAD`·
`MERGE_MSG` 를 지운다.

### 12.3 내용 합치기 — git 의 `xdl_merge`, ZEALOUS 수준

B·O·T 를 §11.1 의 줄로 나눈다.

1. **바뀐 곳 두 목록.** c1 = B→O, c2 = B→T 의 바뀐 곳(§11.2·§11.3 의 편집
   스크립트, B 좌표의 시작·길이와 상대 쪽 좌표의 시작·길이).
2. **짝 맞추기.** 두 목록을 B 좌표로 함께 훑는다.
   - c1 이 c2 보다 **엄격히 앞**(c1 의 끝 < c2 의 시작)이면 c1 을 O 쪽 변경으로 받는다.
     반대도 같다.
   - 아니면(겹치거나 **맞닿으면**) 충돌 후보. 단 두 바뀐 곳의 B 범위가 같고
     바꾼 내용이 바이트까지 같으면 한 번만 받는다("양쪽이 같은 수정").
   - 충돌 후보의 B 범위가 바로 앞 충돌과 겹치거나 맞닿으면 하나로 넓힌다.
   맞닿은 줄의 수정도 충돌이라는 것 — 둘째 줄을 O 가, 셋째 줄을 T 가 고쳐도
   충돌이다 — 은 진짜 git 으로 확인했다(2026-09-18). 한 줄이라도 사이가 뜨면
   충돌이 아니다.
3. **다듬기(refine).** 충돌마다 O 쪽 줄들과 T 쪽 줄들을 §11 로 견준다. 같으면
   충돌이 아니다. 다르면 그 diff 의 바뀐 곳 하나하나가 따로 충돌이 되고, 그
   사이의 같은 줄은 충돌 밖의 보통 줄이 된다 — 그래서 양쪽이 같이 넣은 앞뒤
   줄은 표지 밖으로 나온다.
4. **다시 붙이기(simplify).** 이웃한 두 충돌 사이의 보통 줄이 **3 줄 이하면**
   둘을 한 충돌로 합친다(사이의 줄은 양쪽에 다 들어간다). 4 줄 이상이면 둔다.
   진짜 `git merge` 로 확인한 경계다(1‥3 줄은 붙고 4 줄은 떨어진다, 줄의 글자와
   상관없이). `git merge-file` 은 기본 수준이 달라(ALNUM) 영숫자 없는 줄은 더
   멀리서도 붙인다 — mygit 의 기준은 `git merge` 다.
5. **찍기.** 보통 줄은 그대로, 충돌은:

   ```text
   <<<<<<< HEAD
   <O 쪽 줄들>
   =======
   <T 쪽 줄들>
   >>>>>>> <b 를 준 그대로>
   ```

   (`merge.conflictStyle=merge`, 표지는 7글자.) 충돌 안의 마지막 줄에 줄바꿈이
   없는 입력은 범위 밖이다 — `golden/scen/merge-*.scn` 의 모든 파일은 `\n` 으로 끝난다.

`golden/scen/merge-*.scn` 의 14 장면(PLAN.md §3.1 10단계의 "10 경우" 에 fast-
forward·충돌 풀기·dev 로 합치기·한쪽만 지운 경로를 더했다)은 진짜 `git merge` 가 만든 작업 트리
파일·인덱스(`stage`)·`MERGE_MSG`·머지 커밋 이름(`log`)을 기록한다. mygit 의
결과는 그 넷과 바이트까지 같아야 한다.

---

## 13. 팩

### 13.1 `.pack` (판 2)

| 자리 | 크기 | 내용 |
|---|---|---|
| 0 | 4 | `PACK` |
| 4 | 4 | 판 2 (빅 엔디언) |
| 8 | 4 | 객체 수 |
| 12 | … | 항목들 |
| 끝−20 | 20 | 앞의 모든 바이트의 SHA-1 (= 파일 이름의 체크섬, §5.2) |

**항목 머리** — 첫 바이트: 비트 7 = 뒤에 더 있음, 비트 6‥4 = 형식, 비트 3‥0 =
크기의 낮은 4비트. 뒤따르는 바이트는 비트 7 = 더 있음, 비트 6‥0 = 크기의 다음
7비트(작은 쪽부터). 크기는 **풀었을 때**의 크기다(델타면 델타 데이터의 크기).

| 형식 | 값 | 머리 뒤에 오는 것 |
|---|---|---|
| commit · tree · blob · tag | 1 · 2 · 3 · 4 | zlib 으로 누른 몸 |
| OFS_DELTA | 6 | 뒤로 가는 거리(아래) + zlib 으로 누른 델타 |
| REF_DELTA | 7 | 바탕 객체 이름 20바이트 + zlib 으로 누른 델타 |

(5 는 쓰지 않는다. 만나면 오류.) OFS_DELTA 의 거리 n 은 큰 쪽부터 7비트씩,
비트 7 = 더 있음, 그리고 **이어지는 바이트마다 1 을 더한다**:
`n ← b & 0x7f; b 에 비트 7 이 있는 동안: b ← 다음; n ← ((n + 1) << 7) | (b & 0x7f)`.
바탕의 자리 = 이 항목의 자리 − n.

**델타 데이터** — 바탕 크기, 결과 크기(둘 다 작은 쪽부터 7비트씩, 비트 7 =
더 있음), 그리고 명령들:

| 첫 바이트 | 뜻 |
|---|---|
| `1xxx xxxx` | 복사. 비트 0‥3 이 선 만큼 거리 바이트(작은 쪽부터 최대 4), 비트 4‥6 이 선 만큼 길이 바이트(최대 3)가 뒤따른다. 없는 바이트는 0. 길이가 0 이면 0x10000 |
| `0nnn nnnn` (n ≥ 1) | 끼움. 뒤의 n 바이트를 그대로 |
| `0000 0000` | 예약 — 오류 |

결과의 길이가 머리의 결과 크기와 다르거나 복사가 바탕을 넘어가면 오류.

<!--EX pack-->
```text
$ git verify-pack -v .git/objects/pack/pack-<체크섬>.idx
15ddd0059a37321a05e4e772b98d3380e6785792 commit 215 154 12
a4864a3416732901a8960a8db9c278479f494afa commit 167 124 166
1ae80aa7f830e047934e4641f6c5e34f9a9c53e6 blob   319 102 290
1f837d8cc0ab7283402b4d2b5c299bc390626fdf tree   33 44 392
71e9321a5bb0fcc02694eadb5b8466ad295f3344 tree   33 44 436
bab081fdb7372d4e471fcbb12b886e1a7cddcae2 blob   7 18 480 1 1ae80aa7f830e047934e4641f6c5e34f9a9c53e6
non delta: 5 objects
chain length = 1: 1 object
.git/objects/pack/pack-<체크섬>.pack: ok
# .pack 앞 16바이트 (헤더 12 + 첫 항목)
0000  50 41 43 4b 00 00 00 02 00 00 00 06 97 0d 78 9c  |PACK..........x.|
# .idx 앞 16바이트 (매직 · 판 · fanout[0])
0000  ff 74 4f 63 00 00 00 02 00 00 00 00 00 00 00 00  |.tOc............|
# 파일 이름의 체크섬 = .pack 끝 20바이트: yes
```
<!--/EX-->

(첫 항목 머리 `97 0d`: 비트 6‥4 = 001 commit, 크기 = 7 + 13×16 = 215 — 위
verify-pack 의 첫 줄과 같다.)

### 13.2 `.idx` (판 2)

| 자리 | 크기 | 내용 |
|---|---|---|
| 0 | 4 | `ff 74 4f 63` |
| 4 | 4 | 판 2 |
| 8 | 256×4 | fanout: i 번째 = 첫 바이트가 i 이하인 객체 수 |
| … | N×20 | 객체 이름, 오름차순 |
| … | N×4 | 항목마다 CRC-32(IEEE) — 팩 안 항목의 **날 바이트 전체**(머리·거리/바탕 이름·누른 데이터) |
| … | N×4 | 자리. 비트 31 이 서 있으면 아래 8바이트 표의 번호 |
| … | M×8 | 2 GiB 넘는 자리(mygit 은 읽기만) |
| 끝−40 | 20 | 팩의 체크섬 |
| 끝−20 | 20 | 앞의 모든 바이트의 SHA-1 |

CRC-32 는 Python·Go·Java·TypeScript 는 표준 라이브러리(`zlib.crc32`·
`hash/crc32`·`java.util.zip.CRC32`·node 의 `zlib.crc32`), C++ 은 손으로 짠다.

### 13.3 명령

- `unpack-pack <pack>`: 팩을 앞에서부터 읽어(색인 없이) 모든 객체를 풀고
  델타를 되살려 느슨한 객체로 쓴다. REF_DELTA 의 바탕은 같은 팩이나 저장소에서
  찾는다. 출력 없음.
- `verify-pack -v <idx>`: 진짜 `git verify-pack -v` 와 **바이트까지 같은 출력**.
  팩의 자리 차례로 객체마다
  `<40글자> SP <형식을 6칸 왼쪽 맞춤> SP <크기> SP <팩 안 크기> SP <자리>` 와,
  델타면 ` <사슬 깊이> <바탕 40글자>` 를 더 붙인다. 형식은 되살린 객체의 것이고,
  **크기는 팩 항목 머리에 적힌 크기** — 델타면 되살린 객체가 아니라 델타 데이터의
  크기다(진짜 git 으로 확인, `golden/pack/*.verify`; 위 예시의 `blob 7 18 480` 이
  그것이다). 팩 안 크기 = 다음 항목의 자리(마지막은 끝 체크섬의 자리) − 이 자리.
  그 뒤 `non delta: <n> object(s)` 와 깊이마다 `chain length = <k>: <n> object(s)`
  (1개면 `object`), 마지막으로 `<idx 의 .idx 를 .pack 으로 바꾼 경로>: ok`.
  체크섬·CRC 가 하나라도 틀리면 오류.
- `pack-objects [--delta] <바탕 이름>`: HEAD 와 모든 참조에서 닿는 객체 전부를
  `<바탕 이름>-<체크섬>.pack`·`.idx` 로 쓰고 체크섬을 찍는다. 저장소에 넣으려면
  바탕 이름을 `.git/objects/pack/pack` 으로 준다.

**객체 차례**(다섯 언어가 같아야 한다):

1. 커밋 — HEAD, 그다음 참조 이름 차례의 모든 참조(주석 태그는 벗긴 커밋)를
   시작점으로 넣은 §10.1 의 걷기 차례.
2. 트리와 blob — 1 의 커밋 차례대로, 커밋의 트리를 전위 순회: 트리 자신, 그다음
   항목을 트리 차례로(하위 트리는 재귀). 이미 넣은 것은 건너뛴다.
3. 주석 태그 객체 — 참조 이름 차례.

**델타 고르기**(`--delta` 일 때만, blob 만): 2 에서 blob 을 넣을 때, **같은
경로**로 바로 앞에 넣은 blob 이 있고 그 blob 의 사슬 깊이가 50 미만이면 그것을
바탕으로 델타를 만들어 본다. `2 × 델타 길이 < 몸 길이` 면 OFS_DELTA 로, 아니면
통째로 넣는다. 걷기가 새것부터이므로 옛 판이 새 판을 바탕으로 삼는다(git 과 같은
방향이다 — 10부).

**델타 만들기**(다섯 언어가 같은 바이트를 내야 한다):

```text
바탕을 16바이트 칸으로 자른다: 자리 0, 16, 32, … (16바이트가 다 차는 칸만)
    칸의 바이트 → 그 칸이 처음 나온 자리
i ← 0, 끼울 것 ← 빈 버퍼
i < 결과 길이 동안:
    결과[i‥i+16) 이 칸 표에 있으면 (자리 o):
        L ← 16;  바탕[o+L] = 결과[i+L] 인 동안 L 을 늘린다
        끼울 것을 내보낸다(127 바이트씩 끊어서)
        복사(o, L) 을 내보낸다 — L 이 0x10000 을 넘으면 0x10000 씩 끊는다
        i ← i + L
    아니면: 결과[i] 를 끼울 것에 넣고 i ← i + 1 (127 이 차면 내보낸다)
끼울 것을 내보낸다
```

복사 명령은 0 이 아닌 거리·길이 바이트만 쓴다(비트를 세우지 않은 바이트는
생략). 길이가 정확히 0x10000 이면 길이 바이트를 하나도 쓰지 않는다.

**누른 바이트는 언어마다 다르다**(§3.1) — 그래서 팩 파일과 체크섬도 언어마다
다르다. 같아야 하는 것은 객체 차례·항목 형식·델타 데이터(풀었을 때)·객체 이름
이고, `make parity` 가 `verify-pack -v` 의 이름·형식·크기·깊이·바탕 칸을
견준다(팩 안 크기·자리는 뺀다). 진짜 git 에 대해서는 `git index-pack --strict`
가 받아들이고 `git verify-pack` 이 `ok` 를 내면 통과다.

---

## 14. 전송

### 14.1 pkt-line

`<길이 4자리 소문자 16진><데이터>` — 길이는 **자기 4바이트를 포함한다**. 특별한
값: `0000` flush, `0001` delim(v2 에서 절을 나눈다), `0002` response-end. 한
패킷은 65,520 바이트를 넘지 않는다. 텍스트 패킷은 `\n` 으로 끝나게 보내고,
받을 때는 끝의 `\n` 하나를 떼고 읽는다.

**사이드밴드(side-band-64k)** — v2 의 `packfile` 절에서 각 패킷 데이터의 첫
바이트가 채널이다: 1 = 팩 바이트, 2 = 진행 안내(mygit 은 `no-progress` 를
보내므로 오지 않는다 — 와도 대화 기록에 한 줄로 남길 뿐이다), 3 = 오류
(`fatal: mygit: remote error: <내용>` 으로 끝낸다).

<!--EX pkt-->
```text
# 보낸 것 (ls-refs 요청)
0014command=ls-refs\n
0017object-format=sha1\n
0001
0009peel\n
000csymrefs\n
0000
# 받은 것 (능력 광고 + 참조 목록)
000eversion 2\n
001bagent=git/2.55.0-Linux\n
0013ls-refs=unborn\n
0020fetch=shallow wait-for-done\n
0012server-option\n
0017object-format=sha1\n
0000
0050fd4693d38f3820eb9fb7c198837629bab923893f HEAD symref-target:refs/heads/main\n
003dfd4693d38f3820eb9fb7c198837629bab923893f refs/heads/main\n
0000
```
<!--/EX-->

### 14.2 `clone <path> <dir>` — "멍청한" 로컬 복제

1. `<dir>` 에 §5.1 로 저장소를 만든다. 표준 오류 `Cloning into '<dir>'...`.
2. 원본의 `.git/objects/` 아래 느슨한 객체 파일과 `pack/*.pack`·`*.idx` 를
   **바이트 그대로 복사한다**(협상 없음 — 그래서 "멍청한"). git 의 로컬 복제도
   기본으로 객체 디렉터리를 하드 링크로 가져온다 — 원리는 같다.
3. 원본의 참조(느슨한 파일과 packed-refs, §6.1)를 읽어 `refs/heads/<b>` 는
   `refs/remotes/origin/<b>` 로, `refs/tags/<t>` 는 그대로 쓴다. git 은 이것을
   packed-refs 에 쓰지만 mygit 은 느슨한 파일로 쓴다 — 가리키는 값은 같다.
   `refs/remotes/origin/HEAD` 는 `ref: refs/remotes/origin/<원본 HEAD 의 브랜치>\n`.
4. 원본 HEAD 의 브랜치를 같은 이름으로 만들고 HEAD 를 거기로. reflog 는 HEAD 와
   그 브랜치에 `clone: from <원본 절대 경로>`.
5. `config` 에 git 과 같은 두 절을 붙인다(탭 들여쓰기):

   ```text
   [remote "origin"]
   	url = <원본 절대 경로>
   	fetch = +refs/heads/*:refs/remotes/origin/*
   [branch "<b>"]
   	remote = origin
   	merge = refs/heads/<b>
   ```

6. 그 브랜치를 작업 트리와 인덱스에 쓰고 표준 오류 `done.`

### 14.3 `fetch-pack <path> <ref>…` — 진짜 git 과 v2 로 말하기

`git upload-pack <path>` 를 자식 프로세스로 띄우고(환경에 `GIT_PROTOCOL=version=2`),
그 표준 입출력으로 pkt-line 을 주고받는다(결정 8 — 서버는 진짜 git 이다).

1. 능력 광고를 flush 까지 읽는다. 첫 줄이 `version 2` 가 아니거나 `fetch` 능력이
   없으면 오류.
2. **ls-refs** — 보내는 것은 정확히 이 차례다:
   `command=ls-refs\n` · `object-format=sha1\n` · `0001` · `peel\n` · `symrefs\n` ·
   (`<ref>` 마다) `ref-prefix <ref>\n` · `0000`. 받은 줄 `<40글자> <이름>[ 속성…]`
   을 flush 까지 읽는다.
3. **fetch** — `command=fetch\n` · `object-format=sha1\n` · `0001` · `ofs-delta\n` ·
   `no-progress\n` · (요청한 참조마다, 준 차례, 같은 이름은 한 번) `want <40글자>\n` ·
   (내 저장소의 모든 참조 값마다, 이름 차례, 같은 값은 한 번) `have <40글자>\n` ·
   `done\n` · `0000`. `done` 을 같이 보내므로 협상 왕복 없이 곧바로 팩이 온다.
4. 응답에서 `packfile\n` 절을 찾아 사이드밴드 1 의 바이트를 이어 붙인다. flush 로
   끝난다. 팩의 끝 체크섬을 확인하고 `.git/objects/pack/pack-<체크섬>.pack` 로
   쓴 뒤, 델타를 되살려 객체 이름을 알아내 `.idx` 를 만든다(§13.2).
5. 자식의 표준 입력을 닫고 끝나기를 기다린다. 요청한 참조마다
   `<40글자> <참조 이름>` 을 표준 출력에 찍는다(`git fetch-pack` 과 같은 꼴).
   **참조는 고치지 않는다** — 그것은 `fetch` 의 일이고 mygit 에는 없다.

**대화 기록** — 환경 변수 `MYGIT_PKT_LOG=<파일>` 이 있으면 보내고 받은 패킷을
한 줄에 하나씩 그 파일에 쓴다. 보낸 것은 `> `, 받은 것은 `< ` 로 시작하고, 그
뒤는 §14.1 예시와 같은 꼴(길이 4자리 + 파이썬 `repr` 식 이스케이프)이다. 단
사이드밴드 1 의 팩 바이트는 `< <길이> [pack <n> bytes]` 로 줄여 쓴다.
`golden/pkt/` 의 기록은 이 꼴로 진짜 git 과의 대화를 뜬 것이고, mygit 의 기록은
글자까지 같아야 한다.

---

## 15. 이름표 — 같은 일은 같은 이름으로

부록 A 의 4-up 대조 장(PLAN.md §0.10)은 다섯 언어에서 **같은 개념의 함수를
이름으로 집어** 나란히 싣는다(`<!--CODE sym=…-->`). 그래서 파일과 함수의 이름을
여기서 정한다. 아래 "기준 이름" 을 언어의 관례로 옮긴다:

| 언어 | 파일 | 함수 | 예 (`writeTree`) |
|---|---|---|---|
| Python | `py/mygit/<모듈>.py` | snake_case | `write_tree` |
| TypeScript | `ts/src/<모듈>.ts` | camelCase | `writeTree` |
| Go | `go/<모듈>.go` (패키지 `mygit`) | PascalCase | `WriteTree` |
| Java | `java/mygit/<모듈 PascalCase>.java` (클래스의 static 메서드) | camelCase | `Tree.writeTree` |
| C++ | `cpp/<모듈>.cpp` + `.hpp` (namespace `mygit`) | snake_case | `write_tree` |

| 모듈 | 기준 이름 (§) |
|---|---|
| `sha1` | `sha1(bytes) → 20바이트` · `sha1Hex` · 스트리밍 `Sha1` 형(`update`·`digest`) (§2) |
| `zlib` | `compress` · `decompress` · `decompressPrefix(bytes, 시작) → (바이트, 먹은 수)` · `adler32`; C++ 만 `inflate` · `deflateStored` 를 따로 (§3) |
| `objects` | `hashObject` · `writeObject` · `readObject` · `findObject`(앞부분으로) (§4.6) |
| `tree` | `parseTree` · `serializeTree` · `treeEntryLess` · `writeTree`(인덱스 → 트리) · `flattenTree` (§4.3) |
| `commit` | `parseCommit` · `serializeCommit` · `parseIdent` · `formatDate` · `cleanupMessage` · `subjectOf` (§4.4) |
| `refs` | `readRef` · `resolveRef` · `updateRef` · `readHead` · `listRefs` · `revParse` · `appendReflog` (§6) |
| `index` | `readIndex` · `writeIndex` · `IndexEntry` 형 · `entryFromStat` (§7) |
| `worktree` | `walkWorktree` · `status` · `quotePath` · `checkoutTree` · `switchTo` (§8·§9.3) |
| `walk` | `walkLog` · `mergeBases` · `isAncestor` (§10) |
| `diff` | `splitLines` · `myers` · `compact` · `buildChanges` · `unifiedDiff` · `diffTrees` (§11) |
| `merge` | `merge3` · `mergeTrees` · `mergeCommand` (§12) |
| `pack` | `readPack` · `readIdx` · `applyDelta` · `makeDelta` · `writePack` · `writeIdx` · `verifyPack` (§13) |
| `transport` | `pktLine` · `readPkt` · `cloneLocal` · `fetchPack` (§14) |
| `cli` | `main(args) → 종료 코드` — 명령 해석과 §1.4·§9 의 문장 |

Python 만 `diff` 에 `myersLinear`(middle snake, 결정 7)가 더 있다.

오류는 언어마다 한 가지 형으로 던진다 — `GitError(메시지, 종료 코드)`
(Python 예외 · TypeScript `class GitError extends Error` · Go `*GitError`(error) ·
Java `GitError extends RuntimeException` · C++ `struct GitError`). `cli` 만 그것을
받아 표준 오류에 쓰고 코드로 끝낸다. 다른 모듈은 출력하지 않는다 — 시험이
출력을 가로채지 않고 반환값만 본다.

---

## 16. 시험

### 16.1 어디에

| 언어 | 자리 | 돌리기 |
|---|---|---|
| Python | `py/mygit/tests/test_<모듈>.py` (unittest) | `make test-py` |
| TypeScript | `ts/tests/<모듈>.test.ts` (node:test) | `make test-ts` |
| Go | `go/<모듈>_test.go` | `make test-go` |
| Java | `java/mygit/tests/<모듈>Test.java` + `RunTests.java` (JUnit 없음, 30줄짜리 `Check`, 결정 12) | `make test-java` |
| C++ | `cpp/tests/test_<모듈>.cpp` (한 파일 = 한 실행 파일) | `make test-cpp` |

시험 이름(함수·메서드)은 인용하는 절을 담는다 — 예: `test_s4_3_tree_sort_trap`,
`TestS4_3TreeSortTrap`. 이 덱의 리뷰는 "이 시험은 SPEC 몇 절을 지키나" 를 이름으로
찾는다.

### 16.2 무엇으로 — `golden/`

`golden/` 은 진짜 git 이 만든 기준 바이트다(PLAN.md §5 3단계, `tools/make_golden.py`).
시험은 **그 파일을 읽을 뿐** git 을 부르지 않는다 — git 을 부르는 교차 검사는
`run_all.py` 의 `mygit_*` 실험이 맡는다(PLAN.md §3.1 의 "Oracle check" 칸).

| 파일 | 쓰는 단계 |
|---|---|
| `golden/sha1.tsv` — 100 벡터 (§2, §2.1) | 1 |
| `golden/objects/<이름>` + `objects.tsv`(이름·형식·크기·첫 블록 BTYPE) — git 이 쓴 느슨한 객체 파일 그대로 | 2·3 |
| `golden/stored/<이름>` + `stored_ok.txt` — 저장 블록 zlib 객체와, 그것을 git 이 읽고 `fsck --strict` 한 기록 | 2 |
| `golden/trees/<경우>.tsv`·`.ls` + `trees.tsv` — 트리 12개의 (모드·blob·경로)와 `write-tree` 이름 | 4 |
| `golden/index/plain.bin`(§7.3 으로 지운 것)·`*.raw`(git 이 쓴 그대로: 확장 없음·TREE 확장·판 3)·`ls-stage.txt` | 6 |
| `golden/dag/{equal,dated,criss}/git/` — `.git` 의 HEAD·refs·logs·느슨한 객체, `expect.txt` — `log`·`merge-base` 출력 | 7 |
| `golden/diff/{agree,tie}-NN-<이름>.{a,b,diff}` + `agree.tsv`·`tie.tsv` (§11.2) | 8 |
| `golden/pack/{ofs,ref}.{pack,idx,verify,show-index}` — OFS_DELTA·REF_DELTA 팩, `verify-pack -v`·`show-index` 출력 | 11 |
| `golden/pkt/src/git/` — 원격 저장소, `pkt/<경우>.{log,pack,stdout,args}` — §14.3 의 대화 기록(`args` 는 요청한 참조 한 줄, 로컬이 가진 값 한 줄) | 12 |
| `golden/scen/*.scn` — §16.4 의 장면: `hello`·`plumbing`(5) · `status`(6) · `checkout`(9) · `merge-*`(10) · `clone`(12) · `errors`(전부) | 여럿 |
| `golden/errors.tsv` — `errors` 장면에서 뽑은 §1.4 의 문장·종료 코드 | 전부 |
| `golden/golden.tsv` — 위 파일들의 `파일 · 기대값 · 만든 git 명령`, 첫 줄에 git 판 | 전부 |

### 16.3 먼저 빨갛게

구현을 한 줄도 쓰기 전에 시험을 쓰고, **올바른 까닭으로** 실패하는 것을 본다 —
"모듈이 없다" 는 올바른 까닭이 아니다. 모듈과 함수의 빈 껍데기(`GitError("not
implemented", 99)` 를 던지는)를 먼저 두고, 시험이 "기대한 바이트와 다르다" 나
"not implemented" 로 실패하는 것을 확인한다. 통과시키려고 단언을 느슨하게 하지
않는다(PLAN.md §0.6). git 의 동작이 이 문서와 다르다는 것이 드러나면, 이 문서를
고치고 그 사실을 PLAN.md 의 진행 기록에 남긴다.

### 16.4 장면 파일(`golden/scen/*.scn`) — 명령을 차례로 돌리고 출력을 맞춘다

5·6·7·9·10·12 단계의 시험은 "이 명령들을 차례로 하면 이렇게 찍혀야 한다" 꼴이다.
그것을 언어마다 따로 적지 않도록 장면 파일 하나를 다섯 언어가 같이 읽는다.
장면은 `tools/golden_cases.py` 에 **명령만** 적혀 있고, `tools/make_golden.py`
가 그 명령을 빈 디렉터리에서 진짜 git 으로 돌려 기대 출력을 채운다. 각 언어의
장면 실행기(60줄 남짓)는 같은 명령을 mygit 으로 돌려 한 줄씩 견준다.

| 줄 | 뜻 |
|---|---|
| `# …` · 빈 줄 | 무시 |
| `@date <초>` | 이후 명령의 `GIT_AUTHOR_DATE`·`GIT_COMMITTER_DATE` 를 `<초> +0900` 로 (처음 값 1700000000) |
| `@cd <경로>` | 이후 명령의 현재 디렉터리(장면 뿌리에서의 상대 경로, 처음은 뿌리) |
| `write <경로> <재료>` · `append <경로> <재료>` | 파일 쓰기·덧붙이기. 재료는 §2.1 에 `seq:<a>:<b>`(줄마다 수 하나, a‥b)와 `golden:<golden/ 안 경로>` 를 더한 것. `text:` 안의 `\n \t \\ \xHH` 는 이스케이프 |
| `chmod <경로> 755\|644` · `rm <경로>` · `mkdir <경로>` | 작업 트리 손질 |
| `mygit <인자…>` | 명령 하나. 인자는 공백으로 가르고, `"…"` 로 묶으면 공백을 품는다(안에서 `\"`·`\\`·`\n` 은 이스케이프). 다른 줄(`write` 등)의 경로도 같은 규칙으로 가른다 |
| `cat <경로>` | 파일 내용을 찍는다(실행기가 한다) |
| `stage` | 인덱스를 `git ls-files --stage` 꼴로 찍는다: `%06o SP 40글자 SP 단계 TAB 경로(§8.2)` |
| `ref <rev>` | `<rev>` 를 풀어 40글자를 찍는다(§6.2) |
| `> 줄` · `! 줄` · `= 코드` | 바로 앞 명령의 표준 출력 한 줄 · 표준 오류 한 줄 · 종료 코드 |

- 명령 뒤에 `>` 줄이 없으면 표준 출력은 **비어 있어야** 한다. `!` 도 같다.
  `=` 가 없으면 0 이다.
- 끝 줄바꿈이 없는 출력의 마지막 줄 뒤에는 `%noeol` 한 줄이 붙는다.
- 출력과 인자의 `<ROOT>` 는 장면 뿌리의 절대 경로로 바꿔 읽는다(`init`·`clone`
  의 안내 줄이 절대 경로를 품는다).
- git 으로 돌릴 때 `make_golden.py` 가 바꾸는 것 — **SPEC 의 줄임을 기대 출력에
  옮기는 일이고, 그 밖에는 git 의 출력을 한 글자도 고치지 않는다**:

  | mygit 명령 | 실제로 부르는 git | 기대 출력에서 하는 일 |
  |---|---|---|
  | `init …` | `init -b main …` (§5.1 — mygit 의 기본 브랜치는 언제나 main) | — |
  | `status` | `status --porcelain` | — |
  | `diff …` | `-c diff.indentHeuristic=false diff …` (커밋 둘이면 `--no-renames` 도) | — |
  | `commit …` | 그대로 | 표준 출력의 첫 줄만 남긴다(§9) |
  | `merge <b>` | 그대로 | fast-forward 는 앞 두 줄만, 깨끗한 3-way 는 `Merge made by the 'ort' strategy.` 를 mygit 의 문장으로 바꾸고 변경 통계를 지운다(§12.2) |
  | `stage` · `ref` | `ls-files --stage` · `rev-parse` | — |
