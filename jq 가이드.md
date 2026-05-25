# jq 완벽 가이드

> JSON 필터 명령어 jq 실용서
> 약 30페이지 분량 / jq 1.7 기준

---

## 목차

1. [서문](#1-서문)
2. [jq 시작하기](#2-jq-시작하기)
3. [기본 필터](#3-기본-필터)
4. [객체와 배열 접근](#4-객체와-배열-접근)
5. [파이프와 변환](#5-파이프와-변환)
6. [선택과 조건](#6-선택과-조건)
7. [문자열 처리](#7-문자열-처리)
8. [산술과 집계](#8-산술과-집계)
9. [변수와 바인딩](#9-변수와-바인딩)
10. [함수 정의](#10-함수-정의)
11. [제어 흐름과 재귀](#11-제어-흐름과-재귀)
12. [고급 패턴](#12-고급-패턴)
13. [실전 레시피](#13-실전-레시피)
14. [부록 — 치트시트](#14-부록--치트시트)

---

# 1. 서문

## 1.1 jq란

`jq`는 **JSON을 위한 sed/awk**다. 명령행에서 JSON 데이터를 자르고, 거르고, 변환하고, 합치는 데 특화된 작은 언어이자 도구다.

REST API 응답을 다듬을 때, 로그에서 특정 필드만 추출할 때, AWS CLI/kubectl 출력을 가공할 때 — `jq`를 알면 5분이 5초가 된다.

## 1.2 왜 배워야 하는가

- **API 시대의 필수 도구.** 거의 모든 현대 도구는 JSON으로 출력한다.
- **파이프 친화적.** `curl ... | jq ...` 한 줄로 데이터 파이프라인.
- **함수형 언어.** 짧고 강력한 문법. 한 번 익히면 평생 자산.
- **순수 함수.** 같은 입력엔 같은 출력. 디버깅이 쉽다.

## 1.3 이 책의 약속

모든 예제는 **그대로 복사해서 터미널에 붙여넣으면 동작**한다. `jq` 1.6 이상이면 동일하게 돌아간다(1.7에서 추가된 일부 함수는 표시).

읽기보다 **타이핑**을 권한다. 출력이 어떻게 변하는지 손끝으로 익히는 것이 가장 빠른 길이다.

---

# 2. jq 시작하기

## 2.1 설치

```bash
# Ubuntu/Debian
sudo apt install jq

# macOS
brew install jq

# Windows (Scoop)
scoop install jq

# 버전 확인
jq --version
# jq-1.7.1
```

## 2.2 가장 단순한 사용

`.`은 입력 그대로를 의미하는 항등 필터.

```bash
echo '{"name":"alice","age":30}' | jq '.'
```

출력:

```json
{
  "name": "alice",
  "age": 30
}
```

이미 이것만으로 가치가 있다. **JSON 예쁘게 출력기**(pretty printer).

## 2.3 파일에서 읽기

```bash
jq '.' data.json
```

`-r`을 붙이면 문자열의 따옴표를 제거(raw output).

```bash
echo '"hello"' | jq -r '.'
# hello   ← 따옴표 없음
```

`-c`는 한 줄로 압축(compact).

```bash
echo '{"a":1,"b":2}' | jq -c '.'
# {"a":1,"b":2}
```

## 2.4 자주 쓰는 옵션 한눈에

| 옵션         | 의미                          |
|------------|-----------------------------|
| `-r`       | raw 출력 (문자열 따옴표 제거)         |
| `-c`       | 한 줄로 압축                     |
| `-s`       | 입력 전체를 배열로 묶어서 받음 (slurp)   |
| `-R`       | raw 입력 (각 줄을 문자열로)          |
| `-n`       | null 입력 (입력 안 받음)           |
| `-e`       | 결과가 false/null이면 종료코드 1     |
| `--arg k v` | 변수 `$k`에 문자열 `v` 바인딩       |
| `--argjson k v` | 변수 `$k`에 JSON 값 `v` 바인딩 |
| `--tab`    | 탭으로 들여쓰기                    |
| `--indent N` | N칸 들여쓰기                    |

조합 예:

```bash
# 여러 줄 텍스트를 배열로
echo -e "a\nb\nc" | jq -R -s 'split("\n")'
# ["a", "b", "c", ""]
```

## 2.5 첫 변환

이름만 추출:

```bash
echo '{"name":"alice","age":30}' | jq '.name'
# "alice"

echo '{"name":"alice","age":30}' | jq -r '.name'
# alice
```

여러 필드를 객체로:

```bash
echo '{"name":"alice","age":30,"city":"seoul"}' \
  | jq '{name, city}'
```

```json
{
  "name": "alice",
  "city": "seoul"
}
```

이 단축 문법이 익숙해지면 `jq`가 진짜 빠르게 느껴진다.

---

# 3. 기본 필터

## 3.1 항등 필터 `.`

입력을 그대로 출력.

```bash
echo '42' | jq '.'           # 42
echo '"hi"' | jq '.'         # "hi"
echo '[1,2,3]' | jq '.'      # [1, 2, 3]
```

## 3.2 필드 접근 `.field`

```bash
echo '{"a":1,"b":2}' | jq '.a'      # 1
echo '{"a":1,"b":2}' | jq '.b'      # 2
echo '{"a":1,"b":2}' | jq '.c'      # null
```

존재하지 않는 키는 에러가 아니라 `null`을 낸다. 안전하다.

중첩 필드:

```bash
echo '{"user":{"name":"alice","age":30}}' | jq '.user.name'
# "alice"
```

## 3.3 옵셔널 접근 `.field?`

부재중일 때 에러를 무시하고 비어있는 출력을 낸다.

```bash
echo '[{"a":1},{"b":2}]' | jq '.[].a'
# 1
# null

echo '[{"a":1},{"b":2}]' | jq '.[].a?'
# 1
# null
```

`null`을 아예 빼고 싶다면:

```bash
echo '[{"a":1},{"b":2}]' | jq '.[].a? // empty'
# 1
```

`empty`는 "출력 없음" 값. `//`는 null/false 대체 연산자.

## 3.4 키에 특수문자가 있을 때 `."key"`

```bash
echo '{"first name":"alice"}' | jq '."first name"'
# "alice"

echo '{"foo-bar":1}' | jq '."foo-bar"'
# 1
```

`.["first name"]` 형태도 가능.

## 3.5 배열 접근 `.[N]`

```bash
echo '[10,20,30]' | jq '.[0]'    # 10
echo '[10,20,30]' | jq '.[2]'    # 30
echo '[10,20,30]' | jq '.[-1]'   # 30 (음수 인덱스)
echo '[10,20,30]' | jq '.[100]'  # null
```

## 3.6 배열 슬라이스 `.[lo:hi]`

```bash
echo '[1,2,3,4,5]' | jq '.[1:3]'   # [2, 3]
echo '[1,2,3,4,5]' | jq '.[:2]'    # [1, 2]
echo '[1,2,3,4,5]' | jq '.[3:]'    # [4, 5]
echo '[1,2,3,4,5]' | jq '.[-2:]'   # [4, 5]
```

문자열에도 슬라이스가 된다.

```bash
echo '"hello"' | jq '.[1:4]'   # "ell"
```

## 3.7 모든 원소 펼치기 `.[]`

배열을 **여러 출력**으로 풀어낸다.

```bash
echo '[10,20,30]' | jq '.[]'
# 10
# 20
# 30
```

객체도 가능 (값들만):

```bash
echo '{"a":1,"b":2,"c":3}' | jq '.[]'
# 1
# 2
# 3
```

여기서 jq의 핵심 발상: **출력은 값의 스트림**이다. 하나의 입력에서 여러 출력이 나올 수 있다.

---

# 4. 객체와 배열 접근

## 4.1 키 목록 `keys` / `keys_unsorted`

```bash
echo '{"b":2,"a":1,"c":3}' | jq 'keys'
# ["a", "b", "c"]   ← 정렬됨

echo '{"b":2,"a":1,"c":3}' | jq 'keys_unsorted'
# ["b", "a", "c"]   ← 원래 순서
```

## 4.2 값 목록 `values`

```bash
echo '{"a":1,"b":2}' | jq '[.[]]'
# 또는
echo '{"a":1,"b":2}' | jq 'values'
# 두 번째는 1.7에서 동작이 약간 다르니 [.[]]가 안전
```

## 4.3 키-값 페어 `to_entries` / `from_entries`

```bash
echo '{"a":1,"b":2}' | jq 'to_entries'
```

```json
[
  {"key":"a","value":1},
  {"key":"b","value":2}
]
```

다시 객체로:

```bash
echo '[{"key":"a","value":1},{"key":"b","value":2}]' | jq 'from_entries'
# {"a":1,"b":2}
```

이 패턴은 **객체를 변환할 때** 매우 유용하다.

```bash
# 모든 값을 두 배로
echo '{"a":1,"b":2,"c":3}' | jq '
  to_entries
  | map(.value *= 2)
  | from_entries
'
# {"a":2,"b":4,"c":6}
```

## 4.4 객체 합치기 `+` / `*`

```bash
echo 'null' | jq '{a:1,b:2} + {b:3,c:4}'
# {"a":1,"b":3,"c":4}   ← b는 오른쪽이 이김
```

`*`는 **재귀적 병합** (deep merge):

```bash
echo 'null' | jq '
  {user:{name:"alice",age:30}} * {user:{age:31,city:"seoul"}}
'
# {"user":{"name":"alice","age":31,"city":"seoul"}}
```

`+`는 얕은 병합, `*`는 깊은 병합.

## 4.5 키 / 값 존재 여부 `has`, `in`

```bash
echo '{"a":1}' | jq 'has("a")'      # true
echo '{"a":1}' | jq 'has("b")'      # false

echo '"a"' | jq 'in({"a":1,"b":2})' # true
```

## 4.6 배열 합치기와 연결

```bash
echo 'null' | jq '[1,2] + [3,4]'
# [1,2,3,4]

echo '[[1,2],[3],[4,5]]' | jq 'add'
# [1,2,3,4,5]   ← 모든 원소를 합산/병합
```

`add`는 다재다능하다.

```bash
echo '[1,2,3]' | jq 'add'           # 6 (숫자 합)
echo '["a","b","c"]' | jq 'add'     # "abc" (문자열 연결)
echo '[null,null]' | jq 'add'       # null
```

## 4.7 길이 `length`

```bash
echo '[1,2,3]'      | jq 'length'   # 3
echo '"hello"'      | jq 'length'   # 5
echo '{"a":1,"b":2}'| jq 'length'   # 2 (키 개수)
echo 'null'         | jq 'length'   # 0
```

## 4.8 타입 확인 `type`

```bash
echo '1'       | jq 'type'   # "number"
echo '"hi"'    | jq 'type'   # "string"
echo '[]'      | jq 'type'   # "array"
echo '{}'      | jq 'type'   # "object"
echo 'null'    | jq 'type'   # "null"
echo 'true'    | jq 'type'   # "boolean"
```

## 4.9 경로 표현 `paths`

객체/배열 안의 모든 위치를 길이별로 나열.

```bash
echo '{"a":1,"b":[10,20]}' | jq 'paths'
# ["a"]
# ["b"]
# ["b",0]
# ["b",1]
```

리프 노드만:

```bash
echo '{"a":1,"b":[10,20]}' | jq 'paths(scalars)'
# ["a"]
# ["b",0]
# ["b",1]
```

`getpath` / `setpath`로 동적 접근/수정 가능.

```bash
echo '{"a":{"b":{"c":42}}}' | jq 'getpath(["a","b","c"])'
# 42

echo '{}' | jq 'setpath(["a","b","c"]; 42)'
# {"a":{"b":{"c":42}}}
```

---

# 5. 파이프와 변환

## 5.1 파이프 `|`

쉘 파이프와 똑같다. 왼쪽 출력이 오른쪽 입력.

```bash
echo '{"users":[{"name":"alice"},{"name":"bob"}]}' \
  | jq '.users | .[0] | .name'
# "alice"
```

같은 의미를 한 줄로:

```bash
echo '...' | jq '.users[0].name'
```

복잡할수록 파이프로 끊어 쓰는 편이 가독성이 좋다.

## 5.2 `map(f)` — 배열의 각 원소에 f 적용

```bash
echo '[1,2,3,4]' | jq 'map(. * 2)'
# [2,4,6,8]

echo '[{"name":"a"},{"name":"b"}]' | jq 'map(.name)'
# ["a","b"]
```

`map(f)`는 `[ .[] | f ]`의 단축형이다.

```bash
echo '[1,2,3]' | jq '[ .[] * 2 ]'
# [2,4,6]
```

## 5.3 `select(조건)` — 필터링

```bash
echo '[1,2,3,4,5]' | jq 'map(select(. > 2))'
# [3,4,5]

echo '[{"a":1},{"a":2},{"a":3}]' | jq 'map(select(.a > 1))'
# [{"a":2},{"a":3}]
```

배열을 펼쳐서 필터링하는 패턴도 자주 본다:

```bash
echo '[{"name":"a","active":true},{"name":"b","active":false}]' \
  | jq '.[] | select(.active) | .name'
# "a"
```

## 5.4 `del(경로)` — 삭제

```bash
echo '{"a":1,"b":2,"c":3}' | jq 'del(.b)'
# {"a":1,"c":3}

echo '{"users":[{"name":"a","pw":"x"},{"name":"b","pw":"y"}]}' \
  | jq 'del(.users[].pw)'
# {"users":[{"name":"a"},{"name":"b"}]}
```

## 5.5 갱신 연산 `=`, `|=`, `+=` 등

`=`은 **절대 대입**, `|=`은 **현재 값 기반 변환**.

```bash
echo '{"a":1,"b":2}' | jq '.a = 100'
# {"a":100,"b":2}

echo '{"a":1,"b":2}' | jq '.a |= . + 100'
# {"a":101,"b":2}

echo '{"a":1,"b":2}' | jq '.a += 100'
# {"a":101,"b":2}    ← |=의 단축형
```

배열도 마찬가지:

```bash
echo '{"nums":[1,2,3]}' | jq '.nums |= map(. * 2)'
# {"nums":[2,4,6]}
```

연산자 표:

| 연산자  | 의미                            |
|------|-------------------------------|
| `=`  | 절대 대입                         |
| `|=` | 현재 값을 인자로 변환 후 대입             |
| `+=` | 현재 값에 더하기 (`|= . + ...`)      |
| `-=` | 빼기                            |
| `*=` | 곱하기 / 객체 깊은 병합                |
| `/=` | 나누기                           |
| `%=` | 나머지                           |
| `//=`| null/false면 대체 (`|= . // ...`) |

## 5.6 `walk(f)` — 트리 전체에 적용

모든 하위 노드에 함수를 적용 (1.6+).

```bash
echo '{"a":[1,2],"b":[3,4]}' | jq '
  walk(if type == "number" then . * 10 else . end)
'
# {"a":[10,20],"b":[30,40]}
```

깊이 우선, 후위 순회. 트리 변환의 만능 도구.

---

# 6. 선택과 조건

## 6.1 비교 연산자

```bash
echo 'null' | jq '1 == 1'      # true
echo 'null' | jq '1 != 2'      # true
echo 'null' | jq '1 < 2'       # true
echo 'null' | jq '"a" < "b"'   # true
echo 'null' | jq '[1,2] == [1,2]'  # true (구조적 비교)
```

## 6.2 논리 연산자

```bash
echo 'null' | jq 'true and false'  # false
echo 'null' | jq 'true or false'   # true
echo 'null' | jq 'not'             # true (입력이 null/false면 true)
echo 'true' | jq 'not'             # false
```

`not`은 **함수**라서 파이프로 쓴다.

```bash
echo '5' | jq '. > 10 | not'   # true
```

## 6.3 if-then-else

```bash
echo '5' | jq 'if . > 0 then "positive" elif . < 0 then "negative" else "zero" end'
# "positive"

echo '[1,-1,0,2,-2]' | jq '
  map(if . > 0 then "+" elif . < 0 then "-" else "0" end)
'
# ["+","-","0","+","-"]
```

`elif`는 여러 개 가능. `else`는 필수.

## 6.4 `select(조건)` 깊이 들어가기

```bash
echo '[
  {"name":"alice","age":30,"role":"admin"},
  {"name":"bob","age":25,"role":"user"},
  {"name":"carol","age":35,"role":"admin"}
]' | jq 'map(select(.role == "admin" and .age >= 30))'
```

```json
[
  {"name":"alice","age":30,"role":"admin"},
  {"name":"carol","age":35,"role":"admin"}
]
```

여러 조건을 OR로:

```bash
echo '[1,2,3,4,5]' | jq 'map(select(. == 1 or . == 5))'
# [1,5]
```

## 6.5 `//` 대체 연산자

null/false면 오른쪽으로 대체.

```bash
echo '{"a":null,"b":2}' | jq '.a // "default"'
# "default"

echo '{"a":null,"b":2}' | jq '.b // "default"'
# 2

echo '{}' | jq '.missing // "fallback"'
# "fallback"
```

여러 후보 중 첫 유효값:

```bash
echo '{"primary":null,"backup":"yes"}' | jq '.primary // .backup // "none"'
# "yes"
```

## 6.6 `try`/`catch`

에러를 잡아 기본값으로.

```bash
echo '"hello"' | jq 'try (.[100]) catch "out of range"'
# 문자열에 인덱스는 에러가 아닌데, 진짜 에러 케이스:

echo '1' | jq 'try (. / 0) catch "div by zero"'
# "div by zero"

# 단축형: try
echo '"abc"' | jq 'try .[10]'
# (출력 없음 — 에러는 무시)
```

## 6.7 `empty` — 출력 없음

`empty`는 아무것도 내지 않는 특수 값.

```bash
echo '[1,2,3]' | jq 'map(if . > 1 then . else empty end)'
# [2,3]

echo '[1,2,3]' | jq '.[] | if . > 1 then . else empty end'
# 2
# 3
```

`select`보다 더 일반적인 도구.

---

# 7. 문자열 처리

## 7.1 문자열 연결

```bash
echo 'null' | jq '"hello, " + "world"'
# "hello, world"

echo '{"name":"alice"}' | jq '"Hello, " + .name + "!"'
# "Hello, alice!"
```

## 7.2 문자열 보간 `\(expr)`

```bash
echo '{"name":"alice","age":30}' | jq '"Name: \(.name), Age: \(.age)"'
# "Name: alice, Age: 30"
```

`+`보다 훨씬 깔끔하다.

## 7.3 분할과 결합 `split`, `join`

```bash
echo '"a,b,c,d"' | jq 'split(",")'
# ["a","b","c","d"]

echo '["a","b","c"]' | jq 'join("-")'
# "a-b-c"

echo '["one","two","three"]' | jq 'join(", ")'
# "one, two, three"
```

## 7.4 대소문자 변환

```bash
echo '"Hello"' | jq 'ascii_downcase'   # "hello"
echo '"Hello"' | jq 'ascii_upcase'     # "HELLO"
```

## 7.5 트림과 길이

```bash
echo '"  hello  "' | jq 'ltrimstr(" ")'    # "hello  "  (앞 공백만)
echo '"  hello  "' | jq 'rtrimstr(" ")'    # "  hello"
# 양쪽 트림은 정규식으로:
echo '"  hello  "' | jq 'gsub("^\\s+|\\s+$"; "")'   # "hello"
```

## 7.6 정규식 — `test`, `match`, `capture`

```bash
echo '"hello123"' | jq 'test("[0-9]+")'
# true

echo '"hello123"' | jq 'match("[0-9]+")'
# {"offset":5,"length":3,"string":"123","captures":[]}

echo '"alice@example.com"' | jq '
  capture("(?<user>[^@]+)@(?<domain>.+)")
'
# {"user":"alice","domain":"example.com"}
```

## 7.7 치환 `sub`, `gsub`

```bash
echo '"hello world"' | jq 'sub("world"; "jq")'
# "hello jq"

echo '"a1 b2 c3"' | jq 'gsub("[0-9]"; "X")'
# "aX bX cX"

# 백레퍼런스 (캡처 그룹)
echo '"alice@example.com"' | jq '
  sub("(?<u>[^@]+)@(?<d>.+)"; "user=\(.u), domain=\(.d)")
'
# "user=alice, domain=example.com"
```

## 7.8 시작/끝 검사

```bash
echo '"hello.json"' | jq 'startswith("hello")'   # true
echo '"hello.json"' | jq 'endswith(".json")'     # true
echo '"hello.json"' | jq 'contains("lo.j")'      # true
```

## 7.9 부호화

```bash
echo '"hello world"' | jq '@uri'        # "hello%20world"
echo '"<p>hi</p>"'   | jq '@html'       # "&lt;p&gt;hi&lt;/p&gt;"
echo '"hi"'          | jq '@base64'     # "aGk="
echo '"aGk="'        | jq '@base64d'    # "hi"
echo '["a","b","c"]' | jq '@csv'        # "\"a\",\"b\",\"c\""
echo '["a","b","c"]' | jq '@tsv'        # "a\tb\tc"
echo '"O''Brien"'    | jq '@sh'         # 셸용 인용
```

`@csv` / `@tsv`는 표 데이터 추출에 매우 유용.

## 7.10 문자열 → 숫자 / 숫자 → 문자열

```bash
echo '"42"' | jq 'tonumber'   # 42
echo '42'   | jq 'tostring'   # "42"
echo '"3.14"' | jq 'tonumber' # 3.14
```

---

# 8. 산술과 집계

## 8.1 사칙연산

```bash
echo '10' | jq '. + 5'   # 15
echo '10' | jq '. - 3'   # 7
echo '10' | jq '. * 2'   # 20
echo '10' | jq '. / 4'   # 2.5
echo '10' | jq '. % 3'   # 1
```

## 8.2 수학 함수

```bash
echo '-5'   | jq 'fabs'         # 5
echo '2.7'  | jq 'floor'        # 2
echo '2.3'  | jq 'ceil'         # 3
echo '2.5'  | jq 'round'        # 3
echo '16'   | jq 'sqrt'         # 4
echo '8'    | jq 'log2'         # 3
echo '100'  | jq 'log10'        # 2
echo '2'    | jq 'exp10'        # 100
echo 'null' | jq 'pow(2; 10)'   # 1024
```

## 8.3 최소/최대

```bash
echo '[3,1,4,1,5,9,2,6]' | jq 'min'   # 1
echo '[3,1,4,1,5,9,2,6]' | jq 'max'   # 9

# 키 기반
echo '[{"a":3},{"a":1},{"a":2}]' | jq 'min_by(.a)'
# {"a":1}

echo '[{"a":3},{"a":1},{"a":2}]' | jq 'max_by(.a)'
# {"a":3}
```

## 8.4 합계와 평균

```bash
echo '[1,2,3,4,5]' | jq 'add'
# 15

# 평균은 직접
echo '[1,2,3,4,5]' | jq 'add / length'
# 3
```

조심: 빈 배열은 `add`가 `null`을 낸다.

```bash
echo '[]' | jq 'add // 0'   # 0
```

## 8.5 정렬

```bash
echo '[3,1,4,1,5]' | jq 'sort'
# [1,1,3,4,5]

echo '[3,1,4,1,5]' | jq 'sort | reverse'
# [5,4,3,1,1]

# 키 기반
echo '[{"a":3},{"a":1},{"a":2}]' | jq 'sort_by(.a)'
# [{"a":1},{"a":2},{"a":3}]

# 여러 키
echo '[
  {"name":"a","age":30},
  {"name":"a","age":25},
  {"name":"b","age":20}
]' | jq 'sort_by(.name, .age)'
```

## 8.6 그룹화

```bash
echo '[
  {"team":"A","name":"alice"},
  {"team":"B","name":"bob"},
  {"team":"A","name":"carol"}
]' | jq 'group_by(.team)'
```

```json
[
  [{"team":"A","name":"alice"},{"team":"A","name":"carol"}],
  [{"team":"B","name":"bob"}]
]
```

집계와 결합:

```bash
echo '[
  {"team":"A","score":10},
  {"team":"B","score":5},
  {"team":"A","score":7},
  {"team":"B","score":3}
]' | jq '
  group_by(.team)
  | map({team: .[0].team, total: map(.score) | add})
'
# [{"team":"A","total":17},{"team":"B","total":8}]
```

## 8.7 중복 제거

```bash
echo '[3,1,2,3,1]' | jq 'unique'
# [1,2,3]

echo '[
  {"id":1,"name":"a"},
  {"id":2,"name":"b"},
  {"id":1,"name":"c"}
]' | jq 'unique_by(.id)'
# [{"id":1,"name":"a"},{"id":2,"name":"b"}]
```

## 8.8 숫자 범위 `range`

```bash
echo 'null' | jq '[range(5)]'           # [0,1,2,3,4]
echo 'null' | jq '[range(2;7)]'         # [2,3,4,5,6]
echo 'null' | jq '[range(0;10;2)]'      # [0,2,4,6,8]
echo 'null' | jq '[range(10;0;-2)]'     # [10,8,6,4,2]
```

---

# 9. 변수와 바인딩

## 9.1 `as` 바인딩

값을 변수에 묶어서 재사용.

```bash
echo '5' | jq '. as $x | $x * $x + 1'
# 26
```

여러 변수:

```bash
echo '[1,2,3]' | jq '
  . as $arr
  | $arr | length as $n
  | $arr | add / $n
'
# 2 (평균)
```

## 9.2 분해 바인딩 (1.6+)

```bash
echo '[1,2,3]' | jq '. as [$a, $b, $c] | $a + $b + $c'
# 6

echo '{"x":10,"y":20}' | jq '. as {x: $x, y: $y} | $x + $y'
# 30

# 단축형: 키 이름과 변수명이 같으면
echo '{"x":10,"y":20}' | jq '. as {$x, $y} | $x + $y'
# 30
```

## 9.3 명령행에서 변수 주입

`--arg name value`는 문자열, `--argjson name json`은 JSON.

```bash
echo '[1,2,3,4,5]' | jq --argjson threshold 3 'map(select(. > $threshold))'
# [4,5]

jq --arg name "alice" --argjson age 30 -n '{name: $name, age: $age}'
# {"name":"alice","age":30}
```

`-n`은 입력을 받지 않고 시작.

## 9.4 환경 변수

`$ENV`로 모든 환경변수에 접근.

```bash
HOME=/home/alice jq -n '$ENV.HOME'
# "/home/alice"

# env 함수 (개별 접근)
HOME=/home/alice jq -n 'env.HOME'
```

## 9.5 인자 파일 읽기

```bash
# args.json: {"name":"alice","age":30}
jq --slurpfile args args.json -n '$args[0]'
```

`--slurpfile`은 파일 전체를 배열로 읽는다(`[0]`이 한 입력).

`--rawfile`은 텍스트 그대로:

```bash
jq --rawfile content README.md -n '{readme: $content}'
```

---

# 10. 함수 정의

## 10.1 `def` 문법

```bash
echo 'null' | jq 'def double: . * 2; 5 | double'
# 10
```

여러 줄로:

```bash
echo '[1,2,3,4]' | jq '
  def squared: . * .;
  map(squared)
'
# [1,4,9,16]
```

## 10.2 인자 받기

```bash
echo '5' | jq 'def add(x): . + x; add(10)'
# 15

echo '[1,2,3]' | jq '
  def scale(factor): map(. * factor);
  scale(10)
'
# [10,20,30]
```

`;`이 인자 구분자다 (`,`가 아님 — jq의 `,`는 다른 의미).

## 10.3 여러 인자

```bash
echo '5' | jq '
  def between(lo; hi): . >= lo and . <= hi;
  between(1; 10)
'
# true
```

## 10.4 재귀 함수

```bash
echo 'null' | jq '
  def factorial: if . <= 1 then 1 else . * (. - 1 | factorial) end;
  10 | factorial
'
# 3628800
```

```bash
echo 'null' | jq '
  def fib:
    if . < 2 then .
    else (. - 1 | fib) + (. - 2 | fib)
    end;
  10 | fib
'
# 55
```

## 10.5 내장 함수처럼 사용 가능

함수 정의 후, 파이프와 자유롭게 결합.

```bash
jq -n '
  def is_even: . % 2 == 0;
  def squared: . * .;
  [range(10)]
  | map(select(is_even) | squared)
'
# [0,4,16,36,64]
```

## 10.6 모듈

자주 쓰는 함수는 `.jq` 파일에 모아두고 `import` 가능.

`utils.jq`:
```jq
def double: . * 2;
def add(x): . + x;
```

사용:
```bash
jq 'include "utils"; double | add(1)' <<< '5'
# 11
```

`-L 디렉토리`로 모듈 경로 지정. `~/.jq` 파일은 자동 로드된다.

---

# 11. 제어 흐름과 재귀

## 11.1 `reduce` — 누산

좌측에서 우측으로 접어가며 단일 값으로 축약.

```bash
echo '[1,2,3,4,5]' | jq 'reduce .[] as $x (0; . + $x)'
# 15
```

문법: `reduce 스트림 as $변수 (초기값; 누산식)`

문자열 연결:

```bash
echo '["a","b","c"]' | jq 'reduce .[] as $x (""; . + $x)'
# "abc"
```

객체 만들기:

```bash
echo '[{"k":"a","v":1},{"k":"b","v":2}]' | jq '
  reduce .[] as $item ({}; . + {($item.k): $item.v})
'
# {"a":1,"b":2}
```

## 11.2 `foreach` — 중간값 출력

```bash
echo '[1,2,3,4,5]' | jq 'foreach .[] as $x (0; . + $x)'
# 1
# 3
# 6
# 10
# 15
```

`reduce`와 비슷하지만 매 단계의 누산값을 모두 출력. 누적합 같은 거.

세 번째 인자로 출력 변환식:

```bash
echo '[1,2,3,4,5]' | jq '
  [foreach .[] as $x (0; . + $x; {at: $x, total: .})]
'
# [{"at":1,"total":1},{"at":2,"total":3},...]
```

## 11.3 `repeat` / `until`

```bash
# 처음 5개의 짝수
jq -n '[limit(5; repeat(. + 2; . // 0))]'
# 잘 안 쓰는 패턴이지만 알아두면 좋다

# until: 조건이 참이 될 때까지 반복
jq -n '1 | until(. >= 100; . * 2)'
# 128
```

## 11.4 `recurse(f)` / `..`

값 자기 자신부터, f를 반복 적용해 얻은 모든 결과를 출력.

```bash
echo '5' | jq '[recurse(. - 1; . > 0)]'
# [5,4,3,2,1]
```

`..`는 `recurse`의 단축. 모든 하위 노드 (자신 포함).

```bash
echo '{"a":1,"b":{"c":2,"d":[3,4]}}' | jq '..'
```

```json
{"a":1,"b":{"c":2,"d":[3,4]}}
1
{"c":2,"d":[3,4]}
2
[3,4]
3
4
```

스칼라만:

```bash
echo '{"a":1,"b":{"c":2,"d":[3,4]}}' | jq '[.. | numbers]'
# [1,2,3,4]
```

`numbers`는 입력이 숫자가 아니면 에러를 내는 필터. `.. | numbers`는 트리에서 모든 숫자를 추출하는 관용구.

`strings`, `booleans`, `nulls`, `arrays`, `objects`, `iterables`, `scalars`도 같은 방식.

## 11.5 `limit` — 출력 개수 제한

```bash
jq -n '[limit(5; range(100))]'
# [0,1,2,3,4]
```

무한 스트림에서 N개만 가져올 때 필수.

## 11.6 `first`, `last`, `nth`

```bash
echo '[10,20,30]' | jq 'first(.[])'    # 10
echo '[10,20,30]' | jq 'last(.[])'     # 30
echo '[10,20,30]' | jq 'nth(1; .[])'   # 20
```

배열에는 `.[0]`이 더 직관적이지만, **스트림**에서는 이 함수들이 필요하다.

---

# 12. 고급 패턴

## 12.1 입력 여러 개 받기

기본적으로 jq는 입력 스트림(여러 JSON)을 처리한다.

```bash
echo '1 2 3' | jq '. * 10'
# 10
# 20
# 30
```

전체를 배열로 묶어 받기 (`-s` slurp):

```bash
echo '1 2 3' | jq -s '.'
# [1,2,3]

echo '1 2 3' | jq -s 'add'
# 6
```

## 12.2 NDJSON 처리

한 줄에 하나씩 JSON이 있는 형식. 그대로 파이프하면 된다.

```bash
cat <<EOF | jq 'select(.level == "error") | .msg'
{"level":"info","msg":"started"}
{"level":"error","msg":"db down"}
{"level":"warn","msg":"slow"}
{"level":"error","msg":"timeout"}
EOF
# "db down"
# "timeout"
```

## 12.3 텍스트 → JSON

`-R`로 각 줄을 문자열로 받고, 정제.

```bash
cat <<EOF | jq -R 'split(":") | {user: .[0], shell: .[-1]}'
alice:x:1000:1000::/home/alice:/bin/bash
bob:x:1001:1001::/home/bob:/bin/zsh
EOF
```

```json
{"user":"alice","shell":"/bin/bash"}
{"user":"bob","shell":"/bin/zsh"}
```

`-R -s`로 전체 텍스트를 한 문자열로:

```bash
echo -e "a\nb\nc" | jq -R -s 'split("\n") | map(select(length > 0))'
# ["a","b","c"]
```

## 12.4 키 정렬 / 출력 형식

```bash
echo '{"b":2,"a":1,"c":3}' | jq -S '.'   # 키를 알파벳 순으로
echo '{"a":1}' | jq --tab '.'             # 탭 들여쓰기
echo '{"a":1}' | jq --indent 4 '.'        # 4칸 들여쓰기
```

## 12.5 종료 코드 활용

`-e`는 결과가 null/false일 때 종료코드 1.

```bash
echo '{"active":false}' | jq -e '.active'
echo $?   # 1

echo '{"active":true}' | jq -e '.active'
echo $?   # 0
```

쉘 스크립트의 조건문에 활용:

```bash
if curl -s api/health | jq -e '.ok'; then
    echo "OK"
fi
```

## 12.6 한 입력에서 여러 출력 만들기

`,`는 두 식 모두를 출력.

```bash
echo '{"a":1,"b":2}' | jq '.a, .b'
# 1
# 2

echo '[1,2,3]' | jq '.[0], .[-1]'
# 1
# 3
```

## 12.7 객체 동적 생성

```bash
echo '"hello"' | jq '{(.): length}'
# {"hello":5}

echo '{"name":"alice","age":30}' | jq '
  {(.name): .age}
'
# {"alice":30}
```

`from_entries`와 함께 강력하다:

```bash
echo '[{"id":"a","val":1},{"id":"b","val":2}]' | jq '
  map({key: .id, value: .val}) | from_entries
'
# {"a":1,"b":2}
```

## 12.8 SQL-style JOIN

두 데이터셋을 조인하는 트릭:

```bash
echo 'null' | jq '
  [{"id":1,"name":"alice"},{"id":2,"name":"bob"}] as $users
  | [{"user_id":1,"order":"book"},{"user_id":2,"order":"pen"}] as $orders
  | $orders
  | map(. + {name: ($users[] | select(.id == .user_id) | .name)})
'
```

(실제로는 위 방식이 살짝 까다로워서 인덱싱 후 lookup이 깔끔하다.)

```bash
jq -n '
  {"users": [{"id":1,"name":"alice"},{"id":2,"name":"bob"}],
   "orders":[{"user_id":1,"order":"book"},{"user_id":2,"order":"pen"}]}
  | (.users | map({(.id|tostring): .name}) | add) as $u
  | .orders | map(. + {name: $u[(.user_id|tostring)]})
'
```

```json
[
  {"user_id":1,"order":"book","name":"alice"},
  {"user_id":2,"order":"pen","name":"bob"}
]
```

## 12.9 조건부 갱신

```bash
echo '[
  {"name":"alice","score":95},
  {"name":"bob","score":60},
  {"name":"carol","score":75}
]' | jq '
  map(.grade = (if .score >= 90 then "A"
                elif .score >= 70 then "B"
                else "C" end))
'
```

---

# 13. 실전 레시피

## 13.1 GitHub API 활용

리포지토리 별점 순으로 정렬:

```bash
curl -s 'https://api.github.com/users/torvalds/repos' | jq '
  sort_by(.stargazers_count) | reverse
  | map({name, stars: .stargazers_count, url: .html_url})
  | .[:5]
'
```

이슈 제목과 작성자만:

```bash
curl -s 'https://api.github.com/repos/jqlang/jq/issues' | jq '
  .[] | "\(.number): \(.title) by @\(.user.login)"
'
```

## 13.2 kubectl 출력 다듬기

```bash
# 모든 파드의 이름과 노드 매핑
kubectl get pods -o json | jq '
  .items[] | "\(.metadata.name) -> \(.spec.nodeName)"
'

# 컨테이너 이미지 목록
kubectl get pods -o json | jq -r '
  .items[].spec.containers[].image
' | sort -u
```

## 13.3 AWS CLI

```bash
# EC2 인스턴스 ID와 상태
aws ec2 describe-instances | jq -r '
  .Reservations[].Instances[]
  | "\(.InstanceId)\t\(.State.Name)\t\(.Tags[]?|select(.Key=="Name").Value)"
'

# 비용 절감용: stop된 인스턴스만
aws ec2 describe-instances | jq '
  [.Reservations[].Instances[] | select(.State.Name == "stopped") | .InstanceId]
'
```

## 13.4 Docker

```bash
# 실행 중 컨테이너의 이미지와 이름
docker inspect $(docker ps -q) | jq -r '
  .[] | "\(.Name)\t\(.Config.Image)"
'

# 이미지별 디스크 사용량 정렬
docker system df --format json | jq '
  .Images | sort_by(.Size) | reverse
'
```

## 13.5 로그 분석

NDJSON 로그에서 에러만:

```bash
cat app.log | jq -c '
  select(.level == "error")
  | {time, msg, trace_id}
'
```

특정 사용자 활동:

```bash
cat events.json | jq '
  [.[] | select(.user_id == "alice")]
  | group_by(.event)
  | map({event: .[0].event, count: length})
'
```

## 13.6 CSV 변환

JSON → CSV:

```bash
echo '[
  {"name":"alice","age":30},
  {"name":"bob","age":25}
]' | jq -r '
  (.[0] | keys_unsorted) as $keys
  | $keys, (.[] | [.[$keys[]]])
  | @csv
'
```

```
"name","age"
"alice",30
"bob",25
```

CSV → JSON (외부 도구가 보통 더 낫지만 `jq`로도):

```bash
cat <<EOF | jq -R -s '
  split("\n")
  | map(select(length > 0) | split(","))
  | .[0] as $headers
  | .[1:]
  | map([$headers, .] | transpose | map({(.[0]): .[1]}) | add)
'
name,age
alice,30
bob,25
EOF
```

```json
[
  {"name":"alice","age":"30"},
  {"name":"bob","age":"25"}
]
```

## 13.7 차이 비교

```bash
# a.json과 b.json의 차이
jq -n '
  ($a | to_entries) as $ae
  | ($b | to_entries) as $be
  | {only_in_a: ($ae - $be), only_in_b: ($be - $ae)}
' --slurpfile a a.json --slurpfile b b.json
```

## 13.8 환경설정 머지

기본 + 사용자 설정을 깊은 병합:

```bash
jq -s '.[0] * .[1]' default.json user.json
```

`-s`로 두 파일을 배열로, `*`로 deep merge.

## 13.9 평탄화

중첩 배열 풀기:

```bash
echo '[[1,2],[3,4],[5]]' | jq 'flatten'
# [1,2,3,4,5]

echo '[[[1,2]],[[3,4]]]' | jq 'flatten(1)'
# [[1,2],[3,4]]

echo '[[[1,2]],[[3,4]]]' | jq 'flatten'
# [1,2,3,4]
```

## 13.10 통계 한 줄

```bash
echo '[1,2,3,4,5,6,7,8,9,10]' | jq '
  {
    count: length,
    sum: add,
    min: min,
    max: max,
    avg: (add / length),
    median: (sort | if length % 2 == 0 then (.[length/2-1] + .[length/2]) / 2 else .[length/2 | floor] end)
  }
'
```

```json
{
  "count": 10,
  "sum": 55,
  "min": 1,
  "max": 10,
  "avg": 5.5,
  "median": 5.5
}
```

---

# 14. 부록 — 치트시트

## 14.1 기본 필터

| 필터        | 의미             |
|-----------|----------------|
| `.`       | 입력 그대로         |
| `.foo`    | 객체의 foo 필드     |
| `.foo?`   | foo가 없으면 무시    |
| `.[i]`    | 배열의 i번째        |
| `.[i:j]`  | 배열/문자열 슬라이스    |
| `.[]`     | 배열/객체 펼치기      |
| `..`      | 모든 하위 노드       |

## 14.2 자주 쓰는 함수

| 함수                 | 의미               |
|--------------------|------------------|
| `length`           | 길이/크기            |
| `keys`/`values`    | 키/값 목록           |
| `has(k)`           | 키 존재?            |
| `to_entries`       | {k,v} 배열로        |
| `from_entries`     | 배열에서 객체로         |
| `type`             | 타입 이름            |
| `map(f)`           | 배열에 f 적용         |
| `select(c)`        | 조건 만족만           |
| `del(p)`           | 경로 삭제            |
| `add`              | 합산/연결            |
| `min`/`max`        | 최소/최대            |
| `sort`/`sort_by(f)`| 정렬               |
| `group_by(f)`      | 그룹화              |
| `unique`/`unique_by(f)` | 중복 제거       |
| `range(n)`         | 0..n-1 스트림       |
| `flatten(d)`       | 평탄화 (깊이 d)       |
| `paths`            | 모든 경로            |
| `walk(f)`          | 트리 전체 변환         |
| `recurse(f)`       | 재귀 적용            |
| `reduce ... as $x (init; f)` | 축약        |
| `foreach ... as $x (init; f)` | 매 단계 출력  |

## 14.3 연산자

| 연산자     | 의미                    |
|---------|-----------------------|
| `+`/`-`/`*`/`/`/`%` | 산술                |
| `==`/`!=`/`<`/`>`   | 비교                |
| `and`/`or`/`not`    | 논리                |
| `//`               | null/false면 대체        |
| `|`                | 파이프                   |
| `,`                | 둘 다 출력                |
| `=`                | 절대 대입                  |
| `|=`               | 변환 후 대입               |
| `as`               | 변수 바인딩                |

## 14.4 명령행 옵션

| 옵션          | 의미                  |
|-------------|---------------------|
| `-r`        | raw 문자열 출력          |
| `-R`        | raw 입력 (텍스트)        |
| `-c`        | 컴팩트 (한 줄)           |
| `-s`        | slurp (입력을 배열로)     |
| `-n`        | null 입력             |
| `-e`        | 종료 코드로 결과 표시        |
| `-S`        | 키 정렬                |
| `--tab`     | 탭 들여쓰기              |
| `--indent N`| 들여쓰기 칸 수            |
| `--arg`     | 문자열 변수 주입           |
| `--argjson` | JSON 변수 주입          |
| `--slurpfile` | 파일 → 배열로          |
| `--rawfile` | 파일 → 문자열로          |

## 14.5 한눈에 보는 관용구

```jq
# 모든 leaf 숫자
[.. | numbers]

# 빈 값 제거
map(select(. != null and . != ""))

# 특정 필드 추출
.users | map(.name)

# 객체의 키별 변환
to_entries | map(.value |= ascii_upcase) | from_entries

# 배열의 마지막 N개
.[-N:]

# 객체에 필드 추가
. + {new_field: 42}

# 깊은 병합
.a * .b

# 카운트
group_by(.category) | map({category: .[0].category, count: length})

# 누적합
[foreach .[] as $x (0; . + $x)]
```

## 14.6 디버깅 팁

1. **단계별로 자르기.** 긴 파이프라인에 문제가 있으면 앞부분만 따로 실행해본다.
2. **`debug`** — 입력을 stderr로 출력하고 그대로 통과:

```bash
echo '{"a":1}' | jq '.a | debug | . * 2'
# ["DEBUG:",1]   ← stderr
# 2              ← stdout
```

3. **`--debug-trace`** — 모든 평가 단계 추적 (1.7+).
4. **타입 확인** — 의심되면 `type`을 끼워보자.

## 14.7 학습 리소스

- 공식: <https://jqlang.github.io/jq/manual/>
- 플레이그라운드: <https://jqplay.org>
- jq tutorial: <https://stedolan.github.io/jq/tutorial/>

## 14.8 마치며

jq는 **작고 강력한 언어**다. 이 책의 모든 예제를 직접 쳐봤다면, 이미 일상의 90%는 해결할 수 있다. 나머지는 마주칠 때마다 매뉴얼을 펴서 채우면 된다.

알아두면 좋은 발상의 전환:
- jq는 **함수형 언어**다. 입력을 변수처럼 보지 말고, **흐름**으로 보자.
- 모든 필터는 **스트림을 받아 스트림을 낸다**. 0개, 1개, 여러 개 출력이 모두 자연스럽다.
- 복잡해 보이면 **파이프로 끊어서** 한 단계씩 확인하자.

JSON과 더 친해지길.

— 끝 —

```bash
echo '"jq를 마스터한 당신, 축하합니다 🎉"' | jq -r '.'
```
