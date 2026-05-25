# ripgrep 완벽 가이드

> 가장 빠른 코드 검색 도구 ripgrep 실용서
> 약 30페이지 분량 / ripgrep 14.x 기준

---

## 목차

1. [서문](#1-서문)
2. [ripgrep 시작하기](#2-ripgrep-시작하기)
3. [기본 검색](#3-기본-검색)
4. [정규식 패턴](#4-정규식-패턴)
5. [파일 필터링](#5-파일-필터링)
6. [출력 형식 제어](#6-출력-형식-제어)
7. [컨텍스트 표시](#7-컨텍스트-표시)
8. [대체와 캡처 그룹](#8-대체와-캡처-그룹)
9. [성능과 동작 옵션](#9-성능과-동작-옵션)
10. [설정 파일과 별칭](#10-설정-파일과-별칭)
11. [다른 도구와 결합](#11-다른-도구와-결합)
12. [고급 패턴](#12-고급-패턴)
13. [실전 레시피](#13-실전-레시피)
14. [부록 — 치트시트](#14-부록--치트시트)

---

# 1. 서문

## 1.1 ripgrep이란

`ripgrep`(`rg`)은 Andrew Gallant가 Rust로 만든 **재귀 정규식 검색 도구**다. 디렉토리를 훑으면서 정규식 패턴과 매치되는 줄을 찾는다는 점에서 `grep -r`과 같다. 다른 점은:

- **압도적으로 빠르다.** 대부분의 코드베이스에서 `grep`보다 5-10배, `ag`/`ack`보다 빠르다.
- **`.gitignore`를 자동으로 존중한다.** `node_modules`/`target`/`build`를 신경쓰지 않아도 된다.
- **유니코드를 제대로 처리한다.** UTF-8을 기본 가정.
- **합리적인 기본값.** `--color=auto`, `--smart-case`가 기본.
- **단일 정적 바이너리.** 의존성 없음.

## 1.2 왜 grep을 떠나야 하는가

`grep`은 1973년에 태어난 도구다. 시간이 지나며 GNU grep, BSD grep 등 변종이 생겼고 옵션도 풍부해졌다. 하지만 `grep`은:

1. **`.gitignore`를 모른다** — 매번 `--exclude-dir`를 줄줄이 써야 한다.
2. **느리다** — 큰 monorepo에서 그 차이가 시리얼하게 느껴진다.
3. **이진 파일을 잘못 처리한다** — `--binary-files=without-match` 같은 거 매번 안 쓴다.
4. **regex 엔진이 PCRE2를 기본으로 안 쓴다** — 룩어헤드/룩비하인드 등 한정적.

`ripgrep`은 이 모든 걸 기본값으로 해결한다.

## 1.3 이 책의 약속

모든 예제는 **그대로 복사해서 터미널에 붙여넣으면 동작**한다. 결과는 환경에 따라 색상이 다를 수 있지만 텍스트 자체는 동일하다. ripgrep 13 이상이면 거의 차이 없이 동작한다.

읽기보다 손가락을 움직이길 권한다. `rg`는 **자주 칠수록 빨라지는** 도구다.

---

# 2. ripgrep 시작하기

## 2.1 설치

### 리눅스

```bash
# Ubuntu 22.04+
sudo apt install ripgrep

# Arch
sudo pacman -S ripgrep

# Fedora
sudo dnf install ripgrep

# Cargo (어디서나)
cargo install ripgrep
```

### macOS

```bash
brew install ripgrep
```

### Windows

```powershell
# Scoop
scoop install ripgrep

# Chocolatey
choco install ripgrep

# winget
winget install BurntSushi.ripgrep.MSVC
```

### 버전 확인

```bash
rg --version
# ripgrep 14.1.0
# features:+pcre2
# simd(...)
```

`features:+pcre2`가 보이면 PCRE2가 활성화되어 있다 (`-P` 옵션 가능).

## 2.2 첫 검색

```bash
# 현재 디렉토리에서 "TODO" 검색
rg TODO

# 출력 예시
src/main.rs:42:    // TODO: refactor
src/lib.rs:128:    // TODO: handle errors
```

기본 출력 형식: `파일:줄번호:내용`.

## 2.3 가장 자주 쓰는 옵션 한눈에

| 옵션 | 짧은 형태 | 의미 |
|---|---|---|
| `--ignore-case` | `-i` | 대소문자 무시 |
| `--smart-case` | `-S` | 패턴이 모두 소문자면 무시, 대문자 있으면 구분 |
| `--word-regexp` | `-w` | 단어 경계 매칭 (`foo`가 `foobar`엔 X) |
| `--fixed-strings` | `-F` | 정규식 아닌 리터럴 |
| `--invert-match` | `-v` | 매치 안 되는 줄 |
| `--count` | `-c` | 매치 개수만 |
| `--files-with-matches` | `-l` | 매치된 파일 경로만 |
| `--files` | | 검색할 파일 목록만 (검색 X) |
| `--type RUST` | `-t rust` | 특정 언어만 |
| `--type-not` | `-T` | 제외할 언어 |
| `--glob` | `-g` | 파일 glob 필터 |
| `--hidden` | `.` | 숨김 파일도 |
| `--no-ignore` | `-u` | gitignore 무시 |
| `--context N` | `-C N` | 매치 주변 N줄 |
| `--after-context N` | `-A N` | 매치 뒤 N줄 |
| `--before-context N` | `-B N` | 매치 앞 N줄 |
| `--pcre2` | `-P` | PCRE2 정규식 (룩어헤드 등) |
| `--json` | | JSON 출력 |
| `--replace TEXT` | `-r` | 매치를 TEXT로 대체 |

이 표만 외워도 90%는 끝난다.

## 2.4 도움말 보기

```bash
rg --help        # 짧은 도움말
rg --help-all    # 모든 옵션
man rg           # 매뉴얼 (설치 시)
```

`rg --help`는 자체로 훌륭한 매뉴얼이다.

---

# 3. 기본 검색

## 3.1 단순 패턴

```bash
rg pattern
```

현재 디렉토리부터 재귀적으로 `pattern`을 찾는다. 정규식이지만 영문/숫자/공백만 있다면 사실상 리터럴.

```bash
rg "function"
rg "TODO"
rg "import React"
```

공백/특수문자가 들어가면 따옴표로 감싼다.

## 3.2 검색 디렉토리 지정

```bash
rg pattern path/

# 예시
rg "useState" src/
rg "panic" /var/log/
```

여러 경로:

```bash
rg "TODO" src/ tests/
```

## 3.3 대소문자 처리

```bash
# 정확히 일치 (기본)
rg "Error"

# 무시
rg -i "error"

# 스마트 (소문자만이면 무시, 대문자 있으면 구분)
rg -S "error"   # → "Error", "ERROR", "error" 모두
rg -S "Error"   # → "Error"만
```

`-S`(smart-case)가 가장 실용적이라 별칭으로 기본 적용하는 사람이 많다 (10장 참조).

## 3.4 단어 경계 `-w`

`foo`로 검색했을 때 `foobar`까지 매치되는 게 싫을 때.

```bash
rg "log"     # log, login, logger 모두 매치
rg -w "log"  # log만 매치
```

내부적으로 `\blog\b`와 같다.

## 3.5 리터럴 검색 `-F`

정규식 메타문자가 패턴 안에 있을 때 이스케이프 대신.

```bash
rg "func(a, b)"      # 정규식으로 해석되어 "funca, b" 매치
rg -F "func(a, b)"   # 리터럴 그대로 매치
```

쉘 와일드카드와 헷갈리지 말 것. `*.js` 같은 걸 찾을 땐:

```bash
rg -F "*.js"
```

## 3.6 매치 반전 `-v`

매치되지 **않는** 줄 출력.

```bash
# 빈 줄이 아닌 줄
rg -v "^$"

# "//"로 시작하지 않는 줄
rg -v "^//"
```

## 3.7 stdin에서 읽기

```bash
cat large.log | rg ERROR
ps aux | rg python
```

파일 인자가 없고 stdin이 파이프면 자동으로 stdin 읽음.

## 3.8 한 파일만 검색

```bash
rg pattern file.txt
rg "ERROR" /var/log/syslog
```

## 3.9 매치 개수만

```bash
rg -c "TODO"
# src/main.rs:5
# src/lib.rs:3
```

총합:

```bash
rg -c "TODO" | awk -F: '{s+=$2} END{print s}'
# 또는
rg --count-matches "TODO" | awk -F: '{s+=$2} END{print s}'
```

`-c`는 **매치된 줄 수**, `--count-matches`는 **매치 횟수**(한 줄에 여러 개일 때 모두). 미묘하게 다르다.

## 3.10 매치된 파일 목록만

```bash
rg -l "TODO"
# src/main.rs
# src/lib.rs
```

다른 명령으로 파이프할 때 유용.

```bash
# TODO가 있는 파일만 vim으로 열기
vim $(rg -l "TODO")

# TODO가 있는 모든 파일을 zip으로
rg -l "TODO" | xargs tar czf todos.tar.gz
```

매치 안 된 파일은 `--files-without-match`:

```bash
rg --files-without-match "TODO" src/
```

## 3.11 매치된 부분만 (전체 줄 X)

```bash
rg -o "[A-Z]{3,}"      # 대문자 3+ 토큰만 출력

# 매치 부분만, 줄번호 없이, 정렬
rg -oN "[a-zA-Z_]+" file.txt | sort -u
```

`-N`은 줄번호 숨김, `-H`/`-h`는 파일명 표시/숨김.

---

# 4. 정규식 패턴

## 4.1 ripgrep의 기본 정규식 엔진

ripgrep은 기본으로 Rust의 `regex` 크레이트를 쓴다. 이 엔진은:

- **선형 시간 보장.** 악명 높은 catastrophic backtracking 없음.
- **유니코드 기본 지원.**
- **백레퍼런스/룩어라운드 미지원** (`-P`로 PCRE2 활성화 시 사용 가능).

대부분의 코드 검색은 이 기본 엔진으로 충분하다.

## 4.2 메타문자

```bash
.       # 임의의 한 글자
*       # 0개 이상
+       # 1개 이상
?       # 0개 또는 1개
{n,m}   # n개 이상 m개 이하
^       # 줄 시작
$       # 줄 끝
|       # OR
( )     # 그룹
[ ]     # 문자 클래스
\       # 이스케이프
```

예제:

```bash
# function으로 시작하는 줄
rg "^function"

# ;으로 끝나는 줄
rg ";$"

# foo 또는 bar
rg "foo|bar"

# 숫자만 3-5개
rg "\d{3,5}"

# 정수 매치
rg -w "\d+"
```

## 4.3 문자 클래스

```bash
[abc]        # a, b, 또는 c
[^abc]       # a, b, c가 아닌
[a-z]        # 소문자
[A-Z]        # 대문자
[0-9]        # 숫자
[a-zA-Z0-9_] # 단어 문자
```

축약:

| 축약 | 의미 |
|---|---|
| `\d` | 숫자 `[0-9]` |
| `\D` | 숫자 아닌 |
| `\w` | 단어 문자 `[a-zA-Z0-9_]` |
| `\W` | 단어 문자 아닌 |
| `\s` | 공백 (탭, 스페이스, 개행 등) |
| `\S` | 공백 아닌 |
| `\b` | 단어 경계 |
| `\B` | 단어 경계 아닌 |

```bash
# 16진수 색상 코드
rg "#[0-9a-fA-F]{6}"

# 이메일 (간단)
rg "\w+@\w+\.\w+"

# IPv4 (간단)
rg "\d+\.\d+\.\d+\.\d+"
```

## 4.4 그룹과 OR

```bash
# www. 또는 https:// 로 시작하는 URL
rg "(www\.|https://)\S+"

# get/post/put/delete 메서드
rg "(GET|POST|PUT|DELETE)\s+/"
```

비포획 그룹 `(?:...)`:

```bash
# 뒤에서 캡처할 의도가 없을 때 (성능 미세하게 유리)
rg "(?:Mr|Ms)\. \w+"
```

## 4.5 멀티라인 모드 `-U`

기본적으로 ripgrep은 **줄 단위**로 매치한다. 줄을 가로지르려면 `-U`.

```bash
# 한 줄에서만 매치
rg "function.*\{.*\}"

# 여러 줄 매치
rg -U "function.*\{[\s\S]*?\}"
```

`.`는 기본으로 개행을 매치하지 않는다. `-U`와 함께 `(?s)` 플래그를 쓰거나 `[\s\S]`를 쓰자.

```bash
rg -U "(?s)BEGIN.*?END"
```

## 4.6 인라인 플래그

```
(?i)   대소문자 무시
(?m)   ^/$가 줄마다 (멀티라인)
(?s)   . 이 개행 포함
(?x)   verbose 모드 (공백/주석 허용)
```

```bash
rg "(?i)error"   # = rg -i error
rg "(?ix) ^ \s* (todo|fixme) \b"   # 보기 좋게
```

## 4.7 PCRE2 모드 `-P`

기본 엔진은 빠르지만 룩어라운드와 백레퍼런스가 없다. 필요하면 `-P`.

### 룩어헤드 `(?=...)` / `(?!...)`

```bash
# foo 다음에 bar가 오는 위치의 foo만
rg -P "foo(?=bar)"

# foo 다음에 bar가 안 오는 foo
rg -P "foo(?!bar)"
```

### 룩비하인드 `(?<=...)` / `(?<!...)`

```bash
# bar 앞에 foo가 있는 bar만
rg -P "(?<=foo)bar"
```

### 백레퍼런스 `\1`

```bash
# 같은 단어가 두 번 연속 (typo 잡기)
rg -P "\b(\w+)\s+\1\b"
```

### 명명 그룹

```bash
rg -P "(?<year>\d{4})-(?<month>\d{2})"
```

PCRE2는 미세하게 느리고 catastrophic backtracking 위험이 있다. 필요할 때만 쓰자.

## 4.8 멀티 패턴

여러 패턴 OR로 묶어서 한 번에:

```bash
rg "TODO|FIXME|XXX|HACK"
```

또는 `-e`를 여러 번:

```bash
rg -e TODO -e FIXME -e XXX
```

`-e`는 패턴이 `-`로 시작할 때도 안전하다 (`-` 옵션과 헷갈리지 않음).

```bash
# "-foo"를 검색하려면
rg -e "-foo"
```

파일에서 패턴 읽기 `-f`:

```bash
cat > patterns.txt <<EOF
TODO
FIXME
XXX
HACK
EOF
rg -f patterns.txt
```

---

# 5. 파일 필터링

## 5.1 `.gitignore` 자동 존중

ripgrep의 킬러 기능. `.gitignore`, `.ignore`, `.rgignore`, 글로벌 git ignore까지 모두 존중한다.

```bash
# node_modules, target, build, dist 등 자동 제외
rg "config"
```

git 저장소가 아니어도 `.ignore` 파일은 작동.

## 5.2 모두 검색 `--no-ignore` / `-u`

```bash
rg -u "secret"        # .gitignore 무시
rg -uu "secret"       # .gitignore + 숨김 파일 포함
rg -uuu "secret"      # 위 + 이진 파일까지
```

`-u`를 늘릴수록 검색 범위가 넓어진다. `-uuu`는 사실상 `grep -r`과 동급.

## 5.3 숨김 파일 포함 `--hidden`

```bash
rg --hidden "TODO"     # .git, .env 등도 검색

# 단축
rg . --hidden -l "TODO"
```

`.git/` 등은 보통 `.ignore`로 제외하고 싶다. `~/.ignore`에:

```
.git/
```

라고 적어두면 `--hidden`을 켜도 `.git`은 안 들어간다.

## 5.4 파일 타입 `-t` / `-T`

ripgrep은 흔한 언어/형식의 확장자를 미리 알고 있다.

```bash
# Rust 파일만
rg -t rust "fn main"

# Python만
rg -t py "import"

# 두 개
rg -t rust -t toml "version"

# 제외
rg -T js "console"   # JavaScript 빼고
```

지원되는 타입 보기:

```bash
rg --type-list | head
# agda: *.agda, *.lagda
# aidl: *.aidl
# amake: *.mk, *.mak
# asciidoc: *.adoc, *.asc, *.asciidoc
# ...
```

자주 쓰는 타입: `c`, `cpp`, `rust`, `py`, `js`, `ts`, `go`, `java`, `kotlin`, `swift`, `ruby`, `php`, `html`, `css`, `md`, `yaml`, `json`, `toml`, `xml`, `sh`, `make`, `dockerfile`.

## 5.5 커스텀 타입 추가

```bash
rg --type-add "web:*.{html,css,js,vue,jsx,tsx}" -t web "router"
```

영구적으로 만들려면 설정 파일에 (10장).

## 5.6 glob 필터 `-g`

`.gitignore` 문법과 동일.

```bash
# JS 파일만
rg -g "*.js" "TODO"

# 여러 패턴
rg -g "*.{js,ts}" "TODO"

# 제외 (앞에 ! 붙임)
rg -g "!*.test.js" "TODO"
rg -g "!**/vendor/**" "TODO"

# 특정 폴더만
rg -g "src/**" "TODO"

# 결합
rg -g "*.py" -g "!*_test.py" "import os"
```

`-t`보다 정밀하게 제어할 때 `-g`.

## 5.7 검색 대상 파일 미리 보기 `--files`

검색은 안 하고, **검색했다면 어떤 파일들이 대상이 됐을지** 만 출력.

```bash
rg --files
# 모든 검색 대상 파일 (gitignore 적용)

rg --files -t py
# Python 파일만

rg --files -g "*.md" docs/
```

`fzf`와 결합하면 황금 콤보:

```bash
vim $(rg --files | fzf)
```

또는 다른 도구의 입력으로:

```bash
rg --files -t py | xargs wc -l | sort -n
```

## 5.8 심볼릭 링크 `-L`

기본으로 따라가지 않는다. `-L`로 활성화.

```bash
rg -L "pattern"
```

순환 링크에 주의. ripgrep은 감지해서 경고를 낸다.

## 5.9 깊이 제한 `--max-depth`

```bash
# 현재 디렉토리만 (재귀 X)
rg --max-depth 1 "TODO"

# 2단계까지만
rg --max-depth 2 "TODO"
```

## 5.10 이진 파일 처리

기본으로 이진 파일은 건너뛰고 경고만 낸다.

```bash
# 이진 파일 안의 텍스트 매치
rg --text "string" file.bin

# 또는
rg -a "string" file.bin

# 이진 파일에서 매치되는 파일명만
rg --binary "magic" /usr/bin/
```

---

# 6. 출력 형식 제어

## 6.1 색상 `--color`

```bash
rg --color=auto pattern    # 기본
rg --color=always pattern  # 강제 (파이프해도)
rg --color=never pattern   # 끄기
```

색상 정의 `--colors`:

```bash
rg --colors "match:fg:yellow" --colors "match:style:bold" pattern
```

`<요소>:<속성>:<값>` 형식. 요소: `path`, `line`, `column`, `match`. 속성: `fg`, `bg`, `style`. 값: 색이름 또는 0xHEX.

영구적으론 설정 파일로 (10장).

## 6.2 줄번호 / 파일명

```bash
rg -n pattern    # 줄번호 (기본)
rg -N pattern    # 줄번호 없음
rg -H pattern    # 파일명 강제
rg -h pattern    # 파일명 숨김
rg --column      # 컬럼 번호도
```

## 6.3 통계 `--stats`

```bash
rg --stats pattern src/

# 출력 끝에:
# 152 matches
# 152 matched lines
# 47 files contained matches
# 1024 files searched
# 0 bytes printed
# 12.345678 seconds
```

병목 진단에 유용.

## 6.4 JSON 출력 `--json`

스크립팅에 결정적인 옵션. 각 매치/요약을 JSON 객체로 출력 (NDJSON).

```bash
rg --json "TODO" | head -3
```

```json
{"type":"begin","data":{"path":{"text":"src/main.rs"}}}
{"type":"match","data":{"path":{"text":"src/main.rs"},"lines":{"text":"// TODO\n"},"line_number":42,"absolute_offset":1234,"submatches":[{"match":{"text":"TODO"},"start":3,"end":7}]}}
{"type":"end","data":{"path":{"text":"src/main.rs"},"binary_offset":null,"stats":{"elapsed":{...},...}}}
```

`jq`와 결합:

```bash
# 매치된 줄과 위치만
rg --json "TODO" | jq -r '
  select(.type=="match")
  | "\(.data.path.text):\(.data.line_number): \(.data.lines.text)"
'

# 파일별 매치 수
rg --json "TODO" | jq -r '
  select(.type=="end")
  | "\(.data.path.text)\t\(.data.stats.matches)"
'
```

## 6.5 한 파일 한 줄 `--no-heading`

```bash
rg pattern             # 파일별 헤딩 + 줄들
rg --no-heading pattern  # 모든 줄에 파일명 prefix
rg --heading pattern   # 강제 헤딩
```

기본은 출력 환경에 따라 자동 (TTY면 헤딩, 파이프면 prefix).

## 6.6 정렬 `--sort` / `--sortr`

```bash
# 파일 경로 정렬
rg --sort path "TODO"

# 수정 시간 (오래된 순)
rg --sort modified "TODO"

# 수정 시간 역순 (최근 순)
rg --sortr modified "TODO"
```

지원: `none`(기본), `path`, `modified`, `accessed`, `created`. 정렬은 병렬 처리를 끄므로 약간 느려진다.

## 6.7 줄 길이 제한 `-M`

매치 줄이 너무 길어 화면을 망치는 걸 막는다.

```bash
rg -M 200 pattern   # 200자 넘는 줄은 [Omitted]로 표시

# minified JS 처리할 때 필수
rg -M 200 "function" dist/
```

## 6.8 한 매치당 한 줄로

매치된 텍스트만 추출하는 패턴.

```bash
rg -o --no-line-number --no-filename "[A-Z]{3,}" | sort | uniq -c | sort -rn
```

자주 나오는 약어 빈도 보기.

## 6.9 컬럼 번호

```bash
rg --column "fn main"
# src/main.rs:1:1:fn main() {
```

에디터 점프용으로 유용.

## 6.10 NUL 구분자 `-0` (`--null`)

파일명에 공백/개행이 있을 때 안전한 파이핑.

```bash
rg -l0 "TODO" | xargs -0 sed -i 's/TODO/DONE/g'
```

`-0`은 파일명 뒤에 `\0`을 붙이고, `xargs -0`은 그걸로 구분.

---

# 7. 컨텍스트 표시

매치된 줄 주변 줄도 함께 보고 싶을 때.

## 7.1 `-A` / `-B` / `-C`

```bash
rg -A 3 "ERROR"     # 매치 뒤 3줄 (After)
rg -B 3 "ERROR"     # 매치 앞 3줄 (Before)
rg -C 3 "ERROR"     # 앞뒤 3줄씩
```

## 7.2 컨텍스트 구분자

여러 매치 사이는 `--`로 구분된다.

```bash
$ rg -C 1 "TODO" sample.txt
sample.txt
1-line one
2:line two TODO
3-line three
--
10-line ten
11:line eleven TODO
12-line twelve
```

## 7.3 컨텍스트 안 잘리게

매치 주변에 빈 줄이 있어도 컨텍스트는 끊어지지 않는다.

```bash
rg -C 5 "ERROR"
```

`5`줄을 통째로 가져오므로 다음 매치와 겹칠 수 있다. 이때 ripgrep은 자동으로 합친다.

## 7.4 그룹 모드 `--context-separator`

구분자를 바꾸거나 없앨 수 있다.

```bash
rg -C 2 --context-separator "===" "ERROR"
rg -C 2 --no-context-separator "ERROR"
```

## 7.5 함수 컨텍스트 보기 (의사 패턴)

진정한 "함수 단위" 매치는 멀티라인 정규식이 필요. 간단 버전:

```bash
# 매치 뒤 충분히 긴 컨텍스트로 함수 본체까지
rg -A 30 -t py "def my_function"

# 시작과 끝을 멀티라인으로 잡기 (Rust 함수)
rg -U -t rust "fn \w+\([^)]*\) \{[\s\S]*?\n\}"
```

## 7.6 vimgrep 형식

Vim/Neovim의 quickfix 호환 출력.

```bash
rg --vimgrep "TODO"
# src/main.rs:42:5: // TODO: refactor
```

`파일:줄:컬럼:내용` 형식. Vim에서:

```vim
:cexpr system('rg --vimgrep TODO')
:copen
```

---

# 8. 대체와 캡처 그룹

ripgrep은 검색 도구지만 **대체 미리보기** 기능이 있다. 실제 파일은 수정하지 않는다.

## 8.1 단순 대체 `-r`

```bash
rg "TODO" -r "DONE"
# 매치된 부분만 DONE으로 바꾸어 표시
```

매치 줄 전체가 아니라 **매치된 부분**만 바뀐다.

## 8.2 캡처 그룹 활용

```bash
# 함수 이름 추출
rg "function (\w+)" -r '$1'

# 이름을 다른 형식으로
rg "function (\w+)\((.*)\)" -r 'fn $1($2)'
```

`$1`, `$2`는 캡처 그룹 참조. PCRE2 모드에선 `\1`, `\2`도.

명명 그룹:

```bash
rg "(?<name>\w+)@(?<domain>\S+)" -r '$name AT $domain'
```

## 8.3 매치 부분만 출력 + 변환

```bash
# 모든 함수 정의를 줄바꿈된 목록으로
rg -o "function (\w+)" -r '$1' --no-line-number --no-filename | sort -u
```

## 8.4 실제 파일 수정 (sed와 결합)

ripgrep 자체는 파일을 안 고친다. 결합 패턴:

```bash
# 매치된 파일 목록 → sed로 일괄 치환
rg -l "old_name" | xargs sed -i 's/old_name/new_name/g'

# macOS sed는 -i ''
rg -l "old_name" | xargs sed -i '' 's/old_name/new_name/g'

# 안전하게: NUL 구분자
rg -l0 "old_name" | xargs -0 sed -i 's/old_name/new_name/g'
```

`sd` 도구를 쓰면 더 직관적:

```bash
# brew install sd / cargo install sd
rg -l "old" | xargs sd "old" "new"
```

## 8.5 미리보기 워크플로

```bash
# 1. 무엇이 바뀔지 미리 보기
rg "old_name" -r "new_name"

# 2. 만족하면 실제 적용
rg -l "old_name" | xargs sed -i 's/old_name/new_name/g'
```

---

# 9. 성능과 동작 옵션

## 9.1 ripgrep이 빠른 이유

1. **`.gitignore` 활용으로 검색 대상 자체가 적다.**
2. **메모리 매핑 + SIMD.**
3. **병렬 처리 (디렉토리별 스레드).**
4. **Rust regex의 선형 시간 보장 + DFA 컴파일.**
5. **초기 필터링 (literal prefix를 빠른 검색으로 가지치기).**

## 9.2 스레드 수 `-j`

```bash
rg -j 1 "pattern"   # 단일 스레드
rg -j 8 "pattern"   # 8 스레드
rg -j 0 "pattern"   # 자동 (코어 수)
```

기본은 자동. SSD/NVMe면 그대로 두자. HDD에선 1-2가 더 빠를 수 있다.

## 9.3 mmap vs read

```bash
rg --mmap "pattern"      # 메모리 매핑
rg --no-mmap "pattern"   # read 시스템 콜
```

큰 파일에선 mmap이 빠르지만, 어떤 NFS/네트워크 FS에선 문제가 있다. ripgrep은 보통 자동 결정.

## 9.4 검색 깊이 제한

큰 디렉토리에서:

```bash
rg --max-depth 3 "pattern"
```

## 9.5 매치 수 제한 `-m`

파일당 N개만 매치하고 멈추기.

```bash
rg -m 1 "TODO"        # 파일당 첫 매치만
rg -m 5 "ERROR"       # 파일당 5개까지
```

대형 로그 처리 시 유용.

## 9.6 큰 파일 건너뛰기

```bash
# 1MB 이상은 무시
rg --max-filesize 1M "pattern"
rg --max-filesize 50K "pattern"
```

minified 번들이나 데이터 덤프를 자동으로 거를 수 있다.

## 9.7 행 길이 제한

매치 줄이 너무 길면 매치 자체를 안 하기:

```bash
rg --max-columns 200 "pattern"
rg --max-columns 200 --max-columns-preview "pattern"  # 미리보기만
```

minified 코드에 매치되는 어이없는 결과를 막아준다.

## 9.8 정확한 인코딩 `-E`

```bash
rg -E utf-8 "한글"        # UTF-8 강제
rg -E shift_jis "日本語"
rg -E euc-kr "한글"
```

기본은 UTF-8 + BOM 자동 감지.

## 9.9 압축 파일 검색 `-z`

```bash
rg -z "ERROR" *.log.gz
rg -z "pattern" archive.tar.bz2
```

`gz`, `bz2`, `xz`, `zstd` 등 자동 해제 후 검색. 시스템에 해당 디코더가 있어야 함.

## 9.10 디버그 `--debug`

왜 어떤 파일이 검색되었는지/안 되었는지 추적.

```bash
rg --debug "pattern" 2>&1 | head -20
```

`.gitignore` 적용 흐름까지 보여준다.

---

# 10. 설정 파일과 별칭

## 10.1 환경 변수 `RIPGREP_CONFIG_PATH`

기본 옵션을 파일에 저장.

```bash
# 위치 지정
export RIPGREP_CONFIG_PATH=$HOME/.ripgreprc
```

`.ripgreprc` 예시:

```
# 줄당 한 옵션 (값은 공백으로 구분)
--max-columns=200
--max-columns-preview
--smart-case
--colors=line:fg:yellow
--colors=line:style:bold
--colors=path:fg:cyan
--colors=match:fg:red
--colors=match:style:bold

# 커스텀 타입
--type-add=web:*.{html,css,js,jsx,ts,tsx,vue,svelte}
--type-add=docs:*.{md,mdx,rst,txt,adoc}

# 흔히 무시할 디렉토리
--glob=!.git
--glob=!node_modules
--glob=!target
--glob=!dist
```

`#`은 주석. 이후 `rg`만 입력하면 항상 적용.

확인:

```bash
rg --debug 2>&1 | grep -i config
# config_path: "/home/me/.ripgreprc"
```

## 10.2 `.ignore` 파일

git과 무관한 ripgrep 전용 무시 규칙. `.gitignore` 문법.

프로젝트 루트:
```
# .ignore
*.lock
*.min.js
*.min.css
build/
coverage/
__snapshots__/
```

전역:

```bash
echo "node_modules/" >> ~/.ignore
echo "*.log" >> ~/.ignore
```

## 10.3 `.rgignore`

`.ignore`와 같지만 ripgrep만 보는 파일. `.gitignore`/`.ignore`보다 우선.

## 10.4 쉘 별칭

`.bashrc` / `.zshrc`에:

```bash
# 빠른 변형
alias rgi='rg -i'                    # 대소문자 무시
alias rgw='rg -w'                    # 단어 매칭
alias rgl='rg -l'                    # 파일 목록만
alias rgc='rg -c'                    # 카운트
alias rga='rg -uuu'                  # 모든 파일 (gitignore 무시)
alias rgh='rg --hidden'              # 숨김 포함

# 자주 쓰는 컨텍스트
alias rgcc='rg -C 3'                 # 컨텍스트 3
alias rgvim='rg --vimgrep'           # vim용
```

## 10.5 함수: 매치된 파일 vim으로 열기

```bash
rgv() {
    local files
    files=$(rg -l "$@") || return
    [ -n "$files" ] && vim $files
}

# 사용
rgv "TODO"
```

## 10.6 fzf와 결합

대화형 검색:

```bash
rgfzf() {
    local query="${1:-}"
    rg --line-number --no-heading --color=always --smart-case "${query}" \
      | fzf --ansi \
            --color "hl:-1:underline,hl+:-1:underline:reverse" \
            --delimiter : \
            --preview 'bat --color=always {1} --highlight-line {2}' \
            --preview-window 'right,60%,+{2}/2'
}
```

`bat`는 파일 미리보기용 (없으면 `cat` 대체). `Ctrl-/`로 미리보기 토글, 엔터로 선택.

## 10.7 lazygit, Vim, VS Code

- **VS Code:** Ripgrep을 내부적으로 사용. 자동.
- **Neovim/telescope.nvim:** `live_grep`이 ripgrep 위에서 동작.
- **lazygit:** ripgrep 자동 인식.

이미 매일 쓰고 있을지도 모른다.

---

# 11. 다른 도구와 결합

## 11.1 xargs로 일괄 작업

```bash
# 매치된 파일 vim으로
rg -l "TODO" | xargs vim

# 매치된 파일 백업
rg -l "deprecated" | xargs -I {} cp {} {}.bak

# 매치된 파일 줄 수 합계
rg -l "import" | xargs wc -l | tail -1

# 안전하게 (공백 있는 경로)
rg -l0 "TODO" | xargs -0 vim
```

## 11.2 sed로 치환

```bash
rg -l "old_api" | xargs sed -i 's/old_api/new_api/g'
```

macOS:

```bash
rg -l "old_api" | xargs sed -i '' 's/old_api/new_api/g'
```

## 11.3 git과

```bash
# 변경된 파일에서만 검색
rg "TODO" $(git diff --name-only)

# 스테이지된 파일에서만
rg "console.log" $(git diff --cached --name-only)

# 특정 커밋 이후 변경된 파일
rg "TODO" $(git diff --name-only HEAD~10)
```

## 11.4 fd (find의 대안)

`fd`로 파일을 찾고 ripgrep으로 그 안을 검색:

```bash
fd -e py -e pyx | xargs rg "import os"
```

`fd` 자체가 빠르고 gitignore를 존중한다.

## 11.5 tldr/man 페이지 검색

```bash
man rg | rg "color"
tldr rg | rg "context"
```

## 11.6 awk와

```bash
# 행을 필터링한 후 컬럼 처리
rg "ERROR" /var/log/syslog | awk '{print $1, $2, $5}'

# 매치 부분만 추출 + awk
rg -o "\d+\.\d+\.\d+\.\d+" log.txt | sort | uniq -c | sort -rn | head
```

## 11.7 fzf 결합 (재차)

```bash
# 인터랙티브 코드 점프 (vim 사용)
rg --line-number --no-heading --color=always "" \
  | fzf --ansi --delimiter : \
  | awk -F: '{print "+" $2 " " $1}' \
  | xargs vim
```

## 11.8 entr로 변경 시 자동 재실행

```bash
# .py 파일 변경되면 다시 검색
rg --files -t py | entr -c rg "TODO"
```

## 11.9 GNU parallel과

```bash
# 여러 패턴을 병렬로
parallel -j 4 'rg {} > result_{}.txt' ::: TODO FIXME XXX HACK
```

## 11.10 HTTP API 응답 검색

```bash
curl -s https://api.example.com/users | rg -o '"email":"[^"]+"'
```

`jq`가 더 적절하지만, 빠르게 훑을 땐 ripgrep이 최단거리.

---

# 12. 고급 패턴

## 12.1 멀티라인 매치

```bash
# Python 데코레이터 + 함수 정의
rg -U -t py "@\w+\n+def \w+"

# JS 함수 시그니처가 여러 줄
rg -U "function \w+\(\s*\n[\s\S]*?\)\s*\{"
```

`-U`와 `[\s\S]*?` (lazy) 조합이 핵심.

## 12.2 부정 매치

특정 단어가 같은 줄에 **있되**, 다른 단어는 **없는** 줄.

```bash
# console.log가 있되 // disabled가 없는 줄
rg "console\.log(?!.*// disabled)" -P
```

PCRE2의 룩어헤드 활용. 더 단순하게는 두 단계:

```bash
rg "console\.log" | rg -v "// disabled"
```

## 12.3 매치 횟수 N개 이상인 파일만

ripgrep만으로는 어렵고, 보조 도구 필요:

```bash
rg -c "TODO" | awk -F: '$2 > 5 {print $1}'
# TODO가 5번 넘게 나오는 파일만
```

## 12.4 통계 만들기

```bash
# 함수당 라인 수 추정 (단순)
rg -c "^fn " src/

# import 빈도
rg -oN -t py "^from \S+|^import \S+" | sort | uniq -c | sort -rn

# 가장 긴 줄 찾기
rg --line-buffered ".*" | awk '{print length, $0}' | sort -rn | head
```

## 12.5 코드 리팩토링 보조

```bash
# 사용처 찾기
rg -w "old_function"

# 호출 패턴별
rg "old_function\(\s*\)"        # 인자 없음
rg "old_function\([^,)]+\)"     # 인자 1개
rg "old_function\([^)]+,[^)]+\)" # 인자 2개+

# 정의처와 호출처 구분
rg "fn old_function"           # Rust 정의
rg -w "old_function" -g "!*test*"
```

## 12.6 git 히스토리 탐색

ripgrep은 워킹 디렉토리만 본다. 히스토리는 `git log -G`:

```bash
# "secret" 단어가 추가/삭제된 커밋
git log -G "secret" --oneline

# 특정 커밋의 코드에서 검색
git show <commit>:path/to/file | rg "pattern"
```

## 12.7 패치/diff 검색

```bash
# diff에서 추가된 줄만
git diff | rg "^\+" | rg "TODO"

# 또는
git diff | rg "^\+.*TODO"
```

## 12.8 문서 검색

```bash
# 한글 자료에서
rg "패턴" -t md docs/

# 한국어 단어 빈도 (대략)
rg -oN "[가-힣]+" *.md | sort | uniq -c | sort -rn | head
```

ripgrep은 UTF-8에서 잘 동작. 단어 분리는 별도 NLP 도구가 필요.

## 12.9 정규식 미리 테스트

복잡한 패턴은 작은 입력으로:

```bash
echo 'function foo(a, b) {' | rg -P "function (\w+)\(([\w, ]+)\)"
```

매치되면 확신을 가지고 큰 입력에 적용.

## 12.10 매치를 위치별로

```bash
rg --json "TODO" | jq -r '
  select(.type=="match")
  | "\(.data.path.text):\(.data.line_number):\(.data.submatches[0].start)-\(.data.submatches[0].end)"
'
```

각 매치의 줄/시작/끝 컬럼을 추출 (LSP 같은 도구의 입력으로).

---

# 13. 실전 레시피

## 13.1 코드베이스 첫인상

```bash
# 전체 파일 수
rg --files | wc -l

# 언어별 파일 수
rg --files | rg -o "\.[a-z]+$" | sort | uniq -c | sort -rn

# 줄 수 합계
rg --files -t rust | xargs wc -l | tail -1

# TODO/FIXME 빈도
rg "TODO|FIXME|XXX|HACK" -c | sort -t: -k2 -rn | head

# 가장 큰 파일들
rg --files | xargs wc -l 2>/dev/null | sort -rn | head -10
```

## 13.2 보안 점검

```bash
# 코드 안의 비밀
rg -i "(api[_-]?key|secret|password|token)\s*[=:]" -t py -t js

# 하드코딩된 IP
rg "\b\d{1,3}(\.\d{1,3}){3}\b"

# AWS 액세스 키 패턴
rg "AKIA[0-9A-Z]{16}"

# Slack 토큰
rg "xox[baprs]-[A-Za-z0-9-]+"
```

## 13.3 deprecated 사용처

```bash
# Python 2 잔재
rg -t py "print [^(]"     # print문(괄호 없는)
rg -t py "xrange\("
rg -t py "\.iteritems\(\)"

# jQuery
rg -t js "\\\$\." 

# React class component
rg -t tsx -t jsx "extends React\.Component"
```

## 13.4 의존성 점검

```bash
# package.json에서 특정 패키지 사용처
rg -l "lodash" -t js -t ts

# Cargo.toml의 모든 dependency
rg "^[a-z][a-z0-9_-]+ =" Cargo.toml

# 미사용 import 후보 (단순 휴리스틱)
for file in $(rg -l "import" -t py); do
    rg -o "^import (\w+)$" "$file" -r '$1' | while read mod; do
        if ! rg -q "\b$mod\." "$file"; then
            echo "$file: 사용 안 됨? $mod"
        fi
    done
done
```

## 13.5 로그 분석

```bash
# ERROR 발생 시간대
rg -o "^\[\d{4}-\d{2}-\d{2} \d{2}:" *.log | sort | uniq -c

# 가장 흔한 에러 메시지
rg "ERROR" *.log | rg -o "ERROR.{0,80}" | sort | uniq -c | sort -rn | head

# 특정 사용자의 활동
rg "user_id=alice" *.log | rg -o "action=\w+" | sort | uniq -c

# 5xx 응답
rg "\" 5\d\d " access.log | wc -l
```

## 13.6 마크다운 정리

```bash
# 깨진 링크 패턴
rg -t md "\]\(\)" --line-number

# 헤딩 통계
rg -oN -t md "^#+ " | sort | uniq -c

# 모든 헤딩 추출
rg -oN -t md "^#+ .*"

# TODO가 있는 노트
rg -l "TODO" -t md ~/notes/
```

## 13.7 회고 / 일기 검색

```bash
# 특정 키워드가 있는 일기
rg "운동" -t md ~/journal/ -l

# 월별 빈도
rg "운동" ~/journal/2026/*.md -c | awk -F'[/.:]' '{m=$NF; t+=$NF; print m}'
```

## 13.8 프로젝트 정리

```bash
# 빈 파일 찾기
rg --files -t py | xargs -I {} sh -c 'test ! -s "{}" && echo "{}"'

# 한 줄짜리 파일
for f in $(rg --files -t py); do
    [ $(wc -l < "$f") -eq 0 ] && echo "$f"
done

# 똑같은 함수 이름 중복
rg -oN "fn (\w+)" -r '$1' -t rust | sort | uniq -d
```

## 13.9 GitHub Actions / CI

```bash
# 워크플로 안의 액션 버전
rg "uses: \S+@\S+" .github/

# 환경변수 사용
rg "\\\$\\{\\{.*?\\}\\}" .github/
```

## 13.10 한 줄 통계

```bash
# 코드:주석 비율 (대략, Python)
total=$(rg --files -t py | xargs wc -l | tail -1 | awk '{print $1}')
comments=$(rg -c "^\s*#" -t py | awk -F: '{s+=$2} END {print s}')
echo "주석 비율: $((100 * comments / total))%"
```

---

# 14. 부록 — 치트시트

## 14.1 한 페이지 요약

```
# 기본
rg pattern                  현재 디렉토리에서 검색
rg -i pattern              대소문자 무시
rg -S pattern              스마트 케이스
rg -w pattern              단어 경계
rg -F pattern              리터럴 (정규식 X)
rg -v pattern              매치 안 되는 줄
rg pattern dir/            특정 디렉토리

# 출력
rg -l pattern              파일 목록만
rg -c pattern              파일별 매치 수
rg -o pattern              매치 부분만
rg -n / -N                 줄번호 표시/숨김
rg --column                컬럼 번호
rg --json                  JSON 출력
rg --vimgrep               vim 형식
rg --files                 검색 대상 파일 목록만

# 컨텍스트
rg -A 3 pattern            매치 뒤 3줄
rg -B 3 pattern            매치 앞 3줄
rg -C 3 pattern            앞뒤 3줄

# 파일 필터
rg -t rust pattern         타입 지정
rg -T js pattern           타입 제외
rg -g "*.py" pattern       glob
rg -g "!**/test/**" patt   glob 제외
rg --hidden pattern        숨김 파일도
rg -uuu pattern            모든 파일 (gitignore 무시)
rg --max-depth 2 pattern   깊이 제한
rg --max-filesize 1M pattern  큰 파일 무시

# 정규식
rg "foo|bar"               OR
rg "\d{3}"                 정규식
rg -P "(?<=foo)bar"        PCRE2
rg -U "begin[\s\S]*?end"   멀티라인

# 대체 (미리보기만)
rg "old" -r "new"          대체 표시
rg "(\w+)@(\w+)" -r '$2/$1'  캡처 활용

# 성능
rg -j 8 pattern            스레드 수
rg -m 5 pattern            파일당 매치 제한
rg --no-mmap pattern       mmap 끔
```

## 14.2 파일 타입 (자주 쓰는)

```
c, cpp, h, hpp
rust
py, pyx
js, ts, tsx, jsx
go
java, kotlin, swift
ruby, php
html, css, scss
md, rst
yaml, json, toml, xml
sh, bash, zsh
make, dockerfile, terraform
sql
```

전체: `rg --type-list`

## 14.3 글로벌 설정 템플릿

`~/.ripgreprc`:

```
--smart-case
--max-columns=200
--max-columns-preview
--colors=line:fg:yellow
--colors=line:style:bold
--colors=path:fg:cyan
--colors=path:style:bold
--colors=match:fg:red
--colors=match:style:bold

--type-add=web:*.{html,css,js,jsx,ts,tsx,vue,svelte}
--type-add=docs:*.{md,mdx,rst,txt,adoc}
--type-add=conf:*.{yaml,yml,toml,ini,conf,json}

--glob=!.git
--glob=!node_modules
--glob=!target
--glob=!dist
--glob=!build
--glob=!*.min.js
--glob=!*.min.css
--glob=!package-lock.json
--glob=!yarn.lock
--glob=!*.lock
```

활성화:

```bash
echo 'export RIPGREP_CONFIG_PATH=$HOME/.ripgreprc' >> ~/.bashrc
```

## 14.4 글로벌 무시 파일

`~/.ignore`:

```
.DS_Store
*.swp
*.bak
*.tmp
__pycache__/
.pytest_cache/
.mypy_cache/
.cache/
```

## 14.5 자주 묻는 질문

**Q. 매치가 너무 길어 화면이 깨져요.**
A. `--max-columns 200 --max-columns-preview`. 설정 파일에 박아두자.

**Q. `.gitignore`에 있는 파일도 검색하고 싶어요.**
A. `-u`(한 단계 무시), `-uu`(숨김 포함), `-uuu`(이진 파일까지).

**Q. PCRE2 기능이 동작 안 해요.**
A. `rg --version`에서 `+pcre2` 확인. 없으면 PCRE2 포함된 빌드를 다시 설치.

**Q. 한글이 깨져요.**
A. 터미널 로케일 확인. `LANG=en_US.UTF-8` 또는 `LANG=ko_KR.UTF-8`.

**Q. 너무 빨라서 실수로 큰 변경을 하고 말았어요.**
A. ripgrep은 검색만 하지 변경하지 않는다. 변경은 `sed`/`sd` 등 별도 도구가 한다. 변경 전엔 `git status`로 항상 확인.

**Q. `grep`을 완전히 대체할 수 있나요?**
A. 거의. 다만 POSIX 호환성이 필요한 스크립트, 임베디드 시스템 등에선 `grep`을 그대로 쓴다. 대화형/탐색용으론 ripgrep으로 옮겨가면 안 돌아온다.

## 14.6 학습 리소스

- 공식 GitHub: <https://github.com/BurntSushi/ripgrep>
- 사용자 가이드 (영문): <https://github.com/BurntSushi/ripgrep/blob/master/GUIDE.md>
- 매뉴얼: `man rg` 또는 `rg --help-all`
- 벤치마크/논문: <https://blog.burntsushi.net/ripgrep/>

## 14.7 마치며

`rg`는 **자주 쓸수록 손에 붙는 도구**다. 처음 며칠은 `grep` 습관이 손가락에 남아 있을 것이다. 일주일만 의식적으로 `rg`를 쓰면, 다시 `grep`으로 돌아갔을 때 답답함을 느낀다. 그게 이 도구를 진짜 익혔다는 신호다.

핵심을 다시 짚으면:
- **`-S` (smart-case)** 는 항상 켜둘 만한 기본값
- **`-t / -g`** 로 검색 범위를 좁히면 신호 대 잡음비가 폭발적으로 좋아진다
- **`-l`** 과 **`xargs`** 의 결합은 일괄 작업의 시작
- **설정 파일**(`~/.ripgreprc`)에 자기 취향을 박아두자
- **`--json`** 은 자동화의 문을 연다

당신의 키보드가 더 빨라지길.

— 끝 —

```bash
echo "ripgrep을 마스터한 당신, 축하합니다 🎉"
```
