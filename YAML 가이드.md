# YAML 완벽 가이드

> 사람을 위한 데이터 직렬화 언어, YAML 실용서
> 약 50페이지 분량 / YAML 1.2 기준

---

## 목차

1. [서문](#1-서문)
2. [YAML 시작하기](#2-yaml-시작하기)
3. [스칼라 — 기본 데이터 타입](#3-스칼라--기본-데이터-타입)
4. [시퀀스 — 리스트](#4-시퀀스--리스트)
5. [매핑 — 딕셔너리](#5-매핑--딕셔너리)
6. [블록 스타일 vs 흐름 스타일](#6-블록-스타일-vs-흐름-스타일)
7. [문자열 깊게 다루기](#7-문자열-깊게-다루기)
8. [들여쓰기와 공백](#8-들여쓰기와-공백)
9. [주석](#9-주석)
10. [앵커, 별칭, 병합](#10-앵커-별칭-병합)
11. [태그와 명시적 타입](#11-태그와-명시적-타입)
12. [다중 문서](#12-다중-문서)
13. [YAML과 JSON](#13-yaml과-json)
14. [YAML 1.1 vs 1.2 — 함정](#14-yaml-11-vs-12--함정)
15. [실전 — Docker Compose](#15-실전--docker-compose)
16. [실전 — Kubernetes](#16-실전--kubernetes)
17. [실전 — GitHub Actions](#17-실전--github-actions)
18. [실전 — Ansible](#18-실전--ansible)
19. [실전 — CI/CD 일반](#19-실전--cicd-일반)
20. [실전 — 설정 파일](#20-실전--설정-파일)
21. [도구 — yq](#21-도구--yq)
22. [도구 — yamllint](#22-도구--yamllint)
23. [도구 — 언어별 라이브러리](#23-도구--언어별-라이브러리)
24. [보안과 함정](#24-보안과-함정)
25. [모범 사례](#25-모범-사례)
26. [부록 — 치트시트](#26-부록--치트시트)

---

# 1. 서문

## 1.1 YAML이란

**YAML**은 *YAML Ain't Markup Language*의 재귀 약어다. 사람이 읽고 쓰기 좋은 데이터 직렬화 언어로, 설정 파일과 객체 직렬화에 널리 쓰인다.

처음에는 *Yet Another Markup Language*였지만 — XML과 같은 마크업 언어가 아니라 **데이터** 언어라는 점을 강조하기 위해 이름이 바뀌었다.

확장자는 `.yaml` 또는 `.yml`. 최신 명세는 **YAML 1.2** (2009 발표, 2021 개정).

## 1.2 왜 YAML을 배워야 하는가

현대 인프라 도구의 **공용어**다.

- **Kubernetes** — 모든 매니페스트가 YAML
- **Docker Compose** — `docker-compose.yml`
- **GitHub Actions** — `.github/workflows/*.yml`
- **GitLab CI** — `.gitlab-ci.yml`
- **Ansible** — 플레이북
- **CircleCI / Travis CI / Drone** — 모두 YAML
- **OpenAPI / Swagger** — API 명세
- **Helm Charts** — Kubernetes 패키지
- **Prometheus / Grafana** — 모니터링 설정

DevOps, 클라우드, MLOps, 백엔드를 다룬다면 매일 YAML을 만진다. 모르고 쓰는 것과 알고 쓰는 것의 차이가 크다.

## 1.3 YAML의 철학

YAML은 세 가지를 추구한다.

1. **사람 친화적** — 들여쓰기 기반, 따옴표 최소화
2. **이동성** — 어떤 언어로든 직렬화/역직렬화 가능
3. **표현력** — 그래프, 참조, 다중 문서 지원

JSON이 *기계*의 직렬화 포맷이라면, YAML은 *사람*의 직렬화 포맷이다. 그래서 더 유연하고, 더 위험하다.

## 1.4 이 책의 약속

모든 예제는 **그대로 붙여넣으면 동작**한다. 검증은 다음 도구로:

```bash
# Python으로 파싱 검증
python3 -c "import yaml,sys; print(yaml.safe_load(open('file.yaml')))"

# yq로 JSON 변환 후 jq에 파이프
yq -o=json file.yaml | jq .

# 문법 린트
yamllint file.yaml
```

읽기보다 **타이핑**을 권한다. YAML의 함정은 직접 부딪혀야 기억에 남는다.

## 1.5 책의 구성

전반부(2–14장)는 YAML **언어 자체**를 다룬다. 후반부(15–23장)는 실제 도구에서 어떻게 쓰는지를 다룬다. 24–26장은 함정, 모범 사례, 치트시트다.

순서대로 읽기를 권하지만, 이미 YAML을 써본 독자는 14장(1.1 vs 1.2 함정)과 24장(보안)부터 봐도 좋다.

---

# 2. YAML 시작하기

## 2.1 가장 단순한 YAML

```yaml
name: Alice
age: 30
```

이 두 줄은 다음 JSON과 같다.

```json
{"name": "Alice", "age": 30}
```

핵심은 두 가지.
1. `키: 값` 형태 (콜론 뒤에 **공백 한 칸**)
2. 따옴표는 대부분 **선택**

## 2.2 첫 번째 함정 — 콜론 뒤 공백

```yaml
name:Alice    # 잘못됨 — 키 전체가 "name:Alice"
name: Alice   # 올바름
```

콜론과 값 사이에 **반드시 공백**이 있어야 한다. 없으면 키의 일부로 해석된다.

## 2.3 두 번째 함정 — 들여쓰기

YAML은 **공백으로 구조를 표현**한다. 탭은 **금지**.

```yaml
person:
  name: Alice    # 공백 2개 (4개도 가능, 1개는 권장 안 함)
  age: 30
```

같은 깊이의 항목은 **같은 칸 수**로 들여써야 한다.

```yaml
person:
  name: Alice
   age: 30        # 잘못됨 — 한 칸 더 들어감
```

## 2.4 두 가지 컬렉션

YAML은 두 종류의 컬렉션을 가진다.

**시퀀스(sequence)** — 순서 있는 리스트:

```yaml
- apple
- banana
- cherry
```

**매핑(mapping)** — 키-값 쌍의 모음:

```yaml
fruit: apple
color: red
count: 5
```

이 두 가지를 중첩해서 모든 구조를 표현한다.

## 2.5 중첩 예제

```yaml
person:
  name: Alice
  age: 30
  hobbies:
    - reading
    - cycling
  address:
    city: Seoul
    zip: "06234"
```

JSON으로 변환하면:

```json
{
  "person": {
    "name": "Alice",
    "age": 30,
    "hobbies": ["reading", "cycling"],
    "address": {"city": "Seoul", "zip": "06234"}
  }
}
```

## 2.6 첫 검증

위 YAML을 `person.yaml`로 저장한 뒤:

```bash
python3 -c "import yaml; print(yaml.safe_load(open('person.yaml')))"
```

출력:

```python
{'person': {'name': 'Alice', 'age': 30, 'hobbies': ['reading', 'cycling'], 'address': {'city': 'Seoul', 'zip': '06234'}}}
```

파이썬 딕셔너리/리스트로 그대로 읽힌다. 이게 YAML의 본질이다 — **언어 중립 객체**.

---

# 3. 스칼라 — 기본 데이터 타입

스칼라(scalar)는 더 이상 쪼갤 수 없는 단일 값이다. YAML은 다음 스칼라 타입을 지원한다.

## 3.1 문자열

```yaml
greeting: hello
greeting: "hello"
greeting: 'hello'
```

세 줄 모두 같은 문자열 `hello`다. 따옴표는 일반적으로 **불필요**하지만, 다음 경우엔 **써야 한다**.

```yaml
yes_no: "yes"        # 따옴표 없으면 boolean true로 해석될 수 있음
phone: "010-1234"    # 하이픈 시작은 시퀀스로 오해 가능
zip: "06234"         # 0으로 시작하는 숫자는 8진수로 해석 가능
formula: "1 + 1"     # 그냥은 안전하지만 명시
empty: ""            # 빈 문자열
```

## 3.2 정수

```yaml
decimal: 12345
hex: 0xff           # 255
octal: 0o17         # 15 (YAML 1.2)
binary: 0b1010      # 10 (YAML 1.2)
negative: -42
```

YAML 1.1에서는 8진수가 `0`으로 시작했지만, 1.2에서는 `0o`로 바뀌었다. **이것이 가장 큰 함정** — 14장 참고.

## 3.3 부동소수점

```yaml
pi: 3.14159
exp: 1.2e3          # 1200.0
neg: -0.5
inf: .inf           # 무한대
neg_inf: -.inf
nan: .nan           # Not a Number
```

## 3.4 불리언

```yaml
yes: true
no: false
```

이게 전부다 — **YAML 1.2에서는**. YAML 1.1에서는 다음이 모두 boolean이었다.

```yaml
# YAML 1.1 — 이 모두가 boolean!
a: yes
b: no
c: on
d: off
e: y
f: n
g: True
h: TRUE
```

이걸 **노르웨이 문제(Norway problem)**라 부른다. 노르웨이 국가코드 `NO`를 따옴표 없이 쓰면 `false`가 된다.

```yaml
countries:
  - GB
  - FR
  - NO    # ← 이게 false로 해석됨!
```

해결책은 **따옴표**:

```yaml
countries:
  - GB
  - FR
  - "NO"
```

## 3.5 null

```yaml
a: null
b: ~
c:           # 값이 비어 있어도 null
d: Null
e: NULL
```

다섯 줄 모두 `null`이다. 가장 명시적인 표현은 `null`이지만, 매핑 키 다음에 값을 비워둬도 자동으로 `null`이 된다.

```yaml
settings:
  debug:           # null
  verbose: true
```

## 3.6 날짜와 시간 (YAML 1.1 유산)

```yaml
date: 2024-12-25
datetime: 2024-12-25T10:30:00
datetime_z: 2024-12-25T10:30:00Z
datetime_tz: 2024-12-25T10:30:00+09:00
```

YAML 1.2 스펙에서는 빠졌지만 대부분의 파서가 여전히 지원한다. 안전하게 쓰려면 **문자열로 처리**:

```yaml
release_date: "2024-12-25"
```

## 3.7 타입 추론 — 가장 큰 함정

YAML은 따옴표 없는 값의 타입을 **자동 추론**한다.

```yaml
a: 42          # int
b: 42.0        # float
c: "42"        # string
d: 42 things   # string ("42 things")
e: true        # bool
f: True        # bool
g: TRUE        # bool
h: yes         # YAML 1.1: bool, YAML 1.2: string
i: null        # null
j: ~           # null
k: 2024-01-01  # date or string (구현 의존)
```

**규칙**: 의도가 불명확하면 따옴표를 친다. 특히 사용자 입력 값.

## 3.8 검증 예제

```yaml
types:
  string1: hello
  string2: "hello"
  string3: '42'
  int1: 42
  float1: 3.14
  bool1: true
  null1: ~
  null2:
```

```bash
python3 -c "
import yaml
d = yaml.safe_load(open('types.yaml'))
for k, v in d['types'].items():
    print(f'{k}: {v!r} ({type(v).__name__})')
"
```

출력:

```
string1: 'hello' (str)
string2: 'hello' (str)
string3: '42' (str)
int1: 42 (int)
float1: 3.14 (float)
bool1: True (bool)
null1: None (NoneType)
null2: None (NoneType)
```

## 3.9 정리

| 타입 | 예 | 주의 |
|------|----|----|
| 문자열 | `hello`, `"hi"`, `'hi'` | 모호하면 따옴표 |
| 정수 | `42`, `0xff`, `-1` | `0`-시작은 8진수(1.1) |
| 실수 | `3.14`, `1e3`, `.inf` | `.nan`은 Not a Number |
| 불리언 | `true`, `false` | 1.1에서 yes/no/on/off도 |
| null | `null`, `~`, (빈 값) | 매핑 값 비우면 자동 |
| 날짜 | `2024-12-25` | 문자열로 쓰기 권장 |

---

# 4. 시퀀스 — 리스트

## 4.1 블록 시퀀스

가장 흔한 형태. **하이픈 + 공백**으로 시작.

```yaml
fruits:
  - apple
  - banana
  - cherry
```

JSON: `{"fruits": ["apple", "banana", "cherry"]}`

## 4.2 들여쓰기 — 두 가지 스타일

**스타일 1**: 키와 같은 칸에서 시작 (가장 흔함)

```yaml
fruits:
- apple
- banana
```

**스타일 2**: 키 아래로 들여씀

```yaml
fruits:
  - apple
  - banana
```

둘 다 유효하다. 한 파일 안에서 **일관성**만 지키자. 대부분의 도구(yamllint 기본)는 스타일 2를 권한다.

## 4.3 흐름 시퀀스

JSON처럼 한 줄로 쓸 수 있다.

```yaml
fruits: [apple, banana, cherry]
```

빈 시퀀스:

```yaml
empty: []
```

흐름 스타일 안에서는 따옴표 규칙이 더 엄격하다. 콤마, 대괄호, 콜론이 들어간 값은 따옴표가 필요하다.

```yaml
items: [a, b, "c, d"]    # "c, d"는 한 항목
```

## 4.4 중첩 시퀀스

리스트 안에 리스트.

```yaml
matrix:
  - [1, 2, 3]
  - [4, 5, 6]
  - [7, 8, 9]
```

또는 블록 형식:

```yaml
matrix:
  -
    - 1
    - 2
    - 3
  -
    - 4
    - 5
    - 6
```

블록 형식은 길어서 잘 안 쓴다. 행렬 같은 작은 데이터는 흐름 스타일이 자연스럽다.

## 4.5 시퀀스 안의 매핑

리스트의 각 요소가 객체인 경우 — 매우 흔하다.

```yaml
employees:
  - name: Alice
    age: 30
  - name: Bob
    age: 25
  - name: Carol
    age: 35
```

JSON:

```json
{"employees": [
  {"name": "Alice", "age": 30},
  {"name": "Bob", "age": 25},
  {"name": "Carol", "age": 35}
]}
```

여기서 들여쓰기 요령: **`-`도 한 칸을 차지**한다. 즉, `name`은 `-` 다음 공백 자리에서 시작한다. `age`는 `name`과 같은 열.

```yaml
employees:
  - name: Alice
    age: 30
#   ↑   ↑
#   |   value
#   key (- 자리만큼 들여쓴다)
```

## 4.6 매핑 안의 시퀀스

객체 안의 리스트.

```yaml
person:
  name: Alice
  hobbies:
    - reading
    - cycling
    - cooking
```

여기서도 같은 규칙 — `hobbies`의 값(리스트)은 `name`보다 한 단계 더 들여써야 한다.

## 4.7 깊은 중첩

실전에선 4–5단계 중첩이 자주 나온다.

```yaml
company:
  name: Acme
  departments:
    - name: Engineering
      teams:
        - name: Backend
          members:
            - Alice
            - Bob
        - name: Frontend
          members:
            - Carol
    - name: Marketing
      teams:
        - name: Content
          members:
            - Dave
```

여기서 보이듯, 중첩이 깊어질수록 **들여쓰기 양**이 늘어난다. 한 단계당 공백 2개가 표준.

## 4.8 시퀀스 — 자주 하는 실수

```yaml
# 잘못 — 모두 같은 문자열로 합쳐짐
fruits:
- apple - banana - cherry

# 잘못 — 하이픈 뒤에 공백 없음
fruits:
-apple
-banana

# 올바름
fruits:
- apple
- banana
- cherry
```

```yaml
# 잘못 — 일관성 없는 들여쓰기
fruits:
  - apple
   - banana    # 한 칸 더
  - cherry
```

---

# 5. 매핑 — 딕셔너리

## 5.1 블록 매핑

```yaml
name: Alice
age: 30
city: Seoul
```

각 줄이 키-값 쌍. 키와 값 사이는 `:` + 공백.

## 5.2 흐름 매핑

```yaml
person: {name: Alice, age: 30}
```

빈 매핑:

```yaml
config: {}
```

## 5.3 중첩 매핑

```yaml
person:
  name: Alice
  address:
    city: Seoul
    zip: "06234"
    coordinates:
      lat: 37.5
      lon: 127.0
```

각 단계가 한 단계씩 더 들여써진다.

## 5.4 키의 종류

매핑 키는 보통 문자열이지만, YAML은 임의의 스칼라를 키로 허용한다.

```yaml
42: forty-two           # 정수 키
3.14: pi                # 실수 키
true: yes               # boolean 키 (위험)
null: nothing           # null 키
"with space": ok        # 공백 포함 키
```

대부분의 언어 매핑 타입은 문자열 키를 가정한다. 정수/실수/불리언 키는 **이식성에 문제**를 일으킨다 — 가능하면 문자열로.

## 5.5 복잡한 키

키 자체가 시퀀스나 매핑일 수도 있다 — `?` 문법.

```yaml
? - Alice
  - Bob
: friends
? [Alice, Carol]
: colleagues
```

대부분의 언어가 리스트 키를 지원하지 않으므로 거의 안 쓴다. 알고만 있자.

## 5.6 빈 값

```yaml
a:           # null
b: ~         # null
c: ""        # 빈 문자열
d: []        # 빈 리스트
e: {}        # 빈 매핑
```

이 다섯 개는 **모두 다르다**. JSON으로:

```json
{"a": null, "b": null, "c": "", "d": [], "e": {}}
```

## 5.7 키 충돌

YAML은 **중복 키를 허용한다** — 하지만 동작은 구현 의존.

```yaml
name: Alice
age: 30
name: Bob       # 어느 게 이길까?
```

대부분의 파서는 마지막 값이 이긴다(Bob). 일부는 에러를 낸다. **strict 모드**를 쓰는 yamllint는 경고한다. 절대 의도적으로 쓰지 말자.

## 5.8 매핑 안의 매핑 — 깊은 구조

```yaml
db:
  primary:
    host: db1.local
    port: 5432
    credentials:
      user: admin
      password: secret
  replica:
    host: db2.local
    port: 5432
    credentials:
      user: readonly
      password: ro_secret
```

이런 트리 구조가 YAML이 가장 빛나는 부분이다.

## 5.9 매핑 — 자주 하는 실수

```yaml
# 잘못 — 콜론 뒤에 공백 없음
name:Alice

# 잘못 — 같은 키 두 번
name: Alice
name: Bob       # 위 값을 덮어씀(또는 에러)

# 잘못 — 들여쓰기 불일치
person:
  name: Alice
   age: 30      # 한 칸 더
```

---

# 6. 블록 스타일 vs 흐름 스타일

YAML은 같은 데이터를 두 가지 방식으로 쓸 수 있다.

## 6.1 블록 스타일

들여쓰기로 구조를 표현. 사람이 읽기 좋다.

```yaml
person:
  name: Alice
  hobbies:
    - reading
    - cycling
```

## 6.2 흐름 스타일

JSON과 비슷. 한 줄에 압축.

```yaml
person: {name: Alice, hobbies: [reading, cycling]}
```

흐름 스타일은 사실 **JSON의 상위 집합**이다. 모든 JSON은 유효한 YAML이다 (YAML 1.2 기준).

## 6.3 언제 어느 쪽?

- **블록**: 데이터가 크거나, 사람이 자주 편집할 때 (대부분)
- **흐름**: 짧은 리스트/객체, 임베디드 값

```yaml
# 좋음 — 짧은 리스트는 흐름
ports: [80, 443, 8080]

# 좋음 — 큰 객체는 블록
server:
  host: api.example.com
  port: 443
  tls:
    cert: /etc/ssl/cert.pem
    key: /etc/ssl/key.pem
```

## 6.4 혼합

같은 문서에서 자유롭게 섞을 수 있다.

```yaml
servers:
  - name: web1
    ports: [80, 443]        # 흐름
    tags: [prod, frontend]  # 흐름
  - name: web2
    ports: [80, 443]
    tags: [prod, frontend]
```

## 6.5 흐름 스타일 — 조심할 것

흐름 안에서는 **콤마**가 구분자다. 공백/줄바꿈은 무시된다.

```yaml
# 같은 의미
a: [1, 2, 3]
a: [
  1,
  2,
  3,
]
```

마지막 콤마는 허용되지만 도구별로 다르다. **쓰지 말자**.

흐름 안에 콜론이 들어간 매핑:

```yaml
# 위험 — host:port가 한 토큰으로 보일 수 있음
servers: [host1:8080, host2:8080]

# 안전 — 따옴표
servers: ["host1:8080", "host2:8080"]
```

## 6.6 가독성 비교

같은 데이터, 다섯 가지 표현.

**1. 완전 블록**

```yaml
person:
  name: Alice
  age: 30
  hobbies:
    - reading
    - cycling
```

**2. 매핑은 블록, 시퀀스는 흐름**

```yaml
person:
  name: Alice
  age: 30
  hobbies: [reading, cycling]
```

**3. 흐름 (한 줄)**

```yaml
person: {name: Alice, age: 30, hobbies: [reading, cycling]}
```

**4. 흐름 (여러 줄)**

```yaml
person: {
  name: Alice,
  age: 30,
  hobbies: [reading, cycling]
}
```

**5. JSON과 동일**

```yaml
{"person": {"name": "Alice", "age": 30, "hobbies": ["reading", "cycling"]}}
```

대부분의 인간은 1번이나 2번이 가장 읽기 좋다.

---

# 7. 문자열 깊게 다루기

YAML에서 가장 복잡한 게 문자열이다. 다섯 가지 스타일이 있다.

## 7.1 평범한(plain) 스타일

따옴표 없이.

```yaml
name: Alice
sentence: This is a sentence.
```

장점: 가장 자연스럽다.
단점: 특수 문자 제한, 타입 추론 함정.

다음 문자열은 **평범 스타일로 못 쓴다** (또는 권장하지 않는다):

- 콜론 + 공백을 포함 (`hello: world` → 매핑으로 해석)
- `#`로 시작하거나 공백 + `#` 포함 (주석으로 해석)
- `&`, `*`, `!`, `|`, `>`, `'`, `"`, `%`, `@`, `` ` ``로 시작
- `[`, `]`, `{`, `}`, `,`로 시작
- `- ` (시퀀스 하이픈)
- `?`, `:` 단독
- 숫자/불리언/null로 보이는 값

## 7.2 단일 따옴표

```yaml
greeting: 'Hello, World!'
path: 'C:\Users\Alice'
```

특징: **거의 그대로**. 이스케이프가 거의 없다.

유일한 이스케이프는 `''` (작은 따옴표 두 개 = 작은 따옴표 하나).

```yaml
quote: 'It''s fine.'    # → It's fine.
```

`\n` 같은 백슬래시 이스케이프가 **안 통한다**.

```yaml
text: 'line1\nline2'    # 그대로 "line1\nline2" (개행 아님)
```

## 7.3 큰따옴표

```yaml
greeting: "Hello, World!"
escaped: "line1\nline2\ttabbed"
unicode: "\u00e9"        # é
```

특징: **C 스타일 이스케이프** 모두 지원.

| 이스케이프 | 의미 |
|----------|------|
| `\n` | 개행 |
| `\t` | 탭 |
| `\\` | 백슬래시 |
| `\"` | 큰따옴표 |
| `\0` | NUL |
| `\b` | 백스페이스 |
| `\f` | 폼피드 |
| `\r` | 캐리지 리턴 |
| `\xNN` | 8비트 유니코드 |
| `\uNNNN` | 16비트 유니코드 |
| `\UNNNNNNNN` | 32비트 유니코드 |

윈도우 경로처럼 백슬래시가 많은 문자열은 **단일 따옴표**가 편하다.

```yaml
# 큰따옴표 — 백슬래시 두 번
path: "C:\\Users\\Alice"

# 단일 따옴표 — 그대로
path: 'C:\Users\Alice'
```

## 7.4 리터럴 블록 스칼라 — `|`

여러 줄 문자열, 줄바꿈을 **그대로 보존**.

```yaml
script: |
  #!/bin/bash
  echo "hello"
  echo "world"
```

값은:

```
#!/bin/bash
echo "hello"
echo "world"
```

마지막에 줄바꿈 한 개가 붙는다 (기본 동작).

## 7.5 폴드 블록 스칼라 — `>`

여러 줄을 쓰되, **줄바꿈을 공백으로 합친다**.

```yaml
description: >
  This is a long description
  that wraps across multiple lines
  in the source.
```

값은:

```
This is a long description that wraps across multiple lines in the source.
```

빈 줄은 단락 구분(개행 유지):

```yaml
text: >
  First paragraph
  with two lines.

  Second paragraph.
```

값:

```
First paragraph with two lines.
Second paragraph.
```

## 7.6 블록 스칼라 — chomp 지시자

`|` 와 `>` 뒤에 **chomp 지시자**를 붙여 끝의 개행을 제어한다.

| 지시자 | 이름 | 동작 |
|-------|------|------|
| (기본) | clip | 마지막 개행 1개 유지 |
| `-` | strip | 마지막 개행 모두 제거 |
| `+` | keep | 마지막 개행 모두 유지 |

```yaml
clip: |
  hello
  world
# → "hello\nworld\n"

strip: |-
  hello
  world
# → "hello\nworld"

keep: |+
  hello
  world


# → "hello\nworld\n\n\n"
```

## 7.7 블록 스칼라 — 들여쓰기 지시자

블록 스칼라의 들여쓰기를 **숫자**로 명시.

```yaml
code: |2
    indented with 4 spaces
   indented with 3 spaces
```

여기서 `|2`는 "키 다음 칸에서 +2칸 들여썼다"는 뜻. 잘 안 쓰지만, 첫 줄이 공백으로 시작해 파서가 헷갈릴 때 필요하다.

## 7.8 다섯 스타일 비교

| 스타일 | 특징 | 언제 |
|-------|------|------|
| Plain | 따옴표 없음 | 단순 단어 |
| 단일 따옴표 | 이스케이프 거의 없음 | 백슬래시 많을 때 |
| 큰따옴표 | C 이스케이프 | 제어 문자, 유니코드 |
| Literal `\|` | 개행 보존 | 스크립트, 설정 파일 |
| Folded `>` | 개행 → 공백 | 긴 문장 |

## 7.9 실전 예제

쿠버네티스의 ConfigMap에서 NGINX 설정 임베드:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: nginx-config
data:
  nginx.conf: |
    server {
        listen 80;
        server_name example.com;

        location / {
            proxy_pass http://backend;
        }
    }
```

GitHub Actions에서 멀티라인 스크립트:

```yaml
- name: Run tests
  run: |
    npm install
    npm test
    npm run lint
```

## 7.10 문자열 — 어느 스타일을 고를까

내 경험적 규칙:

1. **단순 단어**(영문/숫자/하이픈) → 평범
2. **사람이 읽을 문장** → 평범 또는 큰따옴표
3. **경로(특히 윈도우)** → 단일 따옴표
4. **이스케이프 필요** → 큰따옴표
5. **여러 줄 + 개행 의미 있음** → `|`
6. **여러 줄 + 자동 줄바꿈** → `>`
7. **타입 충돌 의심** → 따옴표 (예: `"yes"`, `"42"`)

---

# 8. 들여쓰기와 공백

YAML에서 들여쓰기는 **문법**이다. 잘못 쓰면 파싱 실패.

## 8.1 기본 규칙

- **공백만** 사용. 탭은 금지.
- 같은 깊이 항목은 **같은 칸 수**.
- 들여쓰기는 **0보다 큰 수의 공백** (1 이상).

## 8.2 공백 몇 개?

가장 흔한 건 **2개**. 4개도 쓰인다. 1개는 권장 안 함.

```yaml
# 2칸 — 가장 흔함
person:
  name: Alice

# 4칸 — Python 스타일
person:
    name: Alice

# 1칸 — 가능하지만 읽기 어려움
person:
 name: Alice
```

한 파일 안에서 **일관성**만 지키자. 보통 yamllint가 검사한다.

## 8.3 시퀀스의 들여쓰기

시퀀스 하이픈을 키 줄에 맞출지, 들여쓸지 두 스타일.

**스타일 A** — 같은 칸:

```yaml
fruits:
- apple
- banana
```

**스타일 B** — 들여쓴 칸:

```yaml
fruits:
  - apple
  - banana
```

둘 다 올바른 YAML이다. yamllint 기본은 B (`indent-sequences: true`). Ansible 커뮤니티는 B를, 일부 다른 곳은 A를 선호한다.

## 8.4 탭 금지 — 왜?

탭의 너비는 환경마다 다르다(2칸, 4칸, 8칸). YAML은 들여쓰기를 **칸 수**로 비교하기 때문에 탭이 섞이면 모호해진다.

```yaml
# 만약 탭이 허용된다면…
person:
\tname: Alice    # 8칸인지, 4칸인지?
  age: 30        # 2칸. 같은 깊이인가, 다른 깊이인가?
```

해결할 수 없는 문제라서 **YAML이 탭을 통째로 금지**한다.

YAML 안의 **값**(문자열)에는 탭을 쓸 수 있다. 금지된 건 **들여쓰기**용 탭.

## 8.5 에디터 설정

VSCode `settings.json`에 추가:

```json
{
  "[yaml]": {
    "editor.tabSize": 2,
    "editor.insertSpaces": true,
    "editor.detectIndentation": false
  }
}
```

Vim:

```vim
autocmd FileType yaml setlocal ts=2 sts=2 sw=2 expandtab
```

`.editorconfig`:

```ini
[*.{yml,yaml}]
indent_style = space
indent_size = 2
```

## 8.6 들여쓰기 디버깅

들여쓰기 오류는 헷갈린다. 도구를 쓰자.

```bash
# 비주얼 — 공백을 점으로 표시
cat -A file.yaml | head

# 또는
sed 's/ /·/g; s/\t/→/g' file.yaml | head

# yamllint — 가장 강력
yamllint file.yaml
```

## 8.7 공통 함정

**함정 1**: 시퀀스 안의 매핑

```yaml
employees:
  - name: Alice
   age: 30        # 잘못 — name과 같은 칸이어야
```

올바르게:

```yaml
employees:
  - name: Alice
    age: 30
```

**함정 2**: 매핑 값으로 시퀀스

```yaml
hobbies:
- reading        # OK (스타일 A)

hobbies:
  - reading      # OK (스타일 B)

hobbies:
- reading
  - cycling      # 잘못 — 일관성 깨짐
```

**함정 3**: 같은 깊이 다른 칸

```yaml
list:
  - a
   - b           # 잘못 — 한 칸 더
  - c
```

---

# 9. 주석

YAML 주석은 `#`로 시작한다.

## 9.1 기본 형식

```yaml
# 이건 주석
name: Alice    # 줄 끝 주석
```

전용 줄과 줄 끝 모두 가능. `#` 앞에는 **공백 한 칸 이상** 필요(평범 스타일 값에서 `#`가 끼어들지 않도록).

```yaml
url: http://example.com#anchor    # url에 # 포함
```

여기서 `#anchor`는 URL의 일부다(앞에 공백 없음).

```yaml
url: http://example.com #anchor   # url은 http://...com까지, 그 이후는 주석
```

이건 의도와 다를 수 있다. URL에 `#`이 있으면 따옴표:

```yaml
url: "http://example.com#anchor"
```

## 9.2 주석 위치

YAML은 주석을 **데이터로 보존하지 않는다**. 파싱하면 주석은 **사라진다**.

```bash
# config.yaml
# 이 주석은 사라진다
name: Alice
```

```bash
yq -o=json config.yaml
# {"name": "Alice"}
```

이 점이 큰 단점이다. 도구로 YAML을 수정하면 **주석이 날아간다**. `yq`(Go 버전)는 일부 주석 보존을 지원하지만 완벽하진 않다.

## 9.3 주석 스타일

```yaml
###############################
# 섹션 헤더 — 두드러지게
###############################

# 단락 주석
# 여러 줄에 걸쳐 설명할 때
# 자세한 내용 작성

name: Alice    # 줄 끝 — 짧은 설명만
```

## 9.4 주석으로 임시 비활성화

```yaml
servers:
  - host: prod1.example.com
  # - host: prod2.example.com   # 점검 중
  - host: prod3.example.com
```

블록 단위로 주석 처리할 땐 도구 도움을 받자(VSCode: `Ctrl+/`).

## 9.5 주석 — 자주 하는 실수

```yaml
# 잘못 — # 앞에 공백 없으면 주석 아님
name: Alice#some comment

# 올바름
name: Alice  # comment
```

```yaml
# 잘못 — 흐름 컬렉션 안에서도 마찬가지
items: [a, b#bad, c]    # b#bad가 한 토큰

# 올바름
items: [a, b, c]  # 댓글은 밖에서
```

---

# 10. 앵커, 별칭, 병합

YAML의 가장 강력한 기능이다. **반복 제거**의 비밀병기.

## 10.1 앵커와 별칭

`&이름`으로 노드를 표시(앵커), `*이름`으로 참조(별칭).

```yaml
defaults: &defaults
  timeout: 30
  retries: 3
  log_level: info

server1:
  <<: *defaults
  host: srv1.local

server2:
  <<: *defaults
  host: srv2.local
```

해석 결과:

```yaml
server1:
  timeout: 30
  retries: 3
  log_level: info
  host: srv1.local

server2:
  timeout: 30
  retries: 3
  log_level: info
  host: srv2.local
```

`<<: *defaults`가 **병합 키(merge key)** — `defaults`의 모든 키를 펼쳐 넣는다.

## 10.2 단순 별칭

병합 없이 그냥 같은 값을 가리킨다.

```yaml
admin: &admin alice@example.com
contact:
  technical: *admin
  billing: *admin
```

해석:

```yaml
admin: alice@example.com
contact:
  technical: alice@example.com
  billing: alice@example.com
```

이메일을 한 곳에서만 바꾸면 모두 바뀐다.

## 10.3 시퀀스 앵커

```yaml
common_tags: &common
  - production
  - critical

services:
  - name: web
    tags: *common
  - name: api
    tags: *common
```

## 10.4 병합 — 오버라이드

병합한 후 **같은 키를 다시 정의**하면 새 값이 이긴다.

```yaml
defaults: &defaults
  timeout: 30
  retries: 3

slow_server:
  <<: *defaults
  timeout: 120    # 30을 덮어씀
```

해석:

```yaml
slow_server:
  timeout: 120
  retries: 3
```

## 10.5 다중 병합

여러 앵커를 한 번에 병합.

```yaml
base: &base
  timeout: 30
  retries: 3

logging: &logging
  log_level: info
  log_path: /var/log/app

server1:
  <<: [*base, *logging]
  host: srv1.local
```

해석:

```yaml
server1:
  timeout: 30
  retries: 3
  log_level: info
  log_path: /var/log/app
  host: srv1.local
```

여러 앵커에 같은 키가 있으면 **앞쪽이 이긴다**(파서 따라 다름. PyYAML은 뒤쪽이 이긴다 — 항상 동작 확인).

## 10.6 중첩 앵커

앵커 안에서 다른 앵커를 참조.

```yaml
db_base: &db_base
  port: 5432
  driver: postgres

db_prod: &db_prod
  <<: *db_base
  host: prod.db.local
  pool: 20

services:
  api:
    db:
      <<: *db_prod
      database: api_prod
  worker:
    db:
      <<: *db_prod
      database: worker_prod
```

해석:

```yaml
services:
  api:
    db:
      port: 5432
      driver: postgres
      host: prod.db.local
      pool: 20
      database: api_prod
  worker:
    db:
      port: 5432
      driver: postgres
      host: prod.db.local
      pool: 20
      database: worker_prod
```

## 10.7 앵커 — 함정

**함정 1**: 병합 키 `<<`는 **YAML 1.1**의 비공식 기능이다. YAML 1.2 명세에서는 빠졌지만, 대부분의 파서가 지원한다. 단, **GitHub Actions는 지원 안 함**.

```yaml
# .github/workflows/x.yml — 병합 키 안 통함
defaults: &defaults
  runs-on: ubuntu-latest
jobs:
  test:
    <<: *defaults    # ← GitHub Actions에선 에러
```

**함정 2**: `*alias`로 받은 값은 **참조**이지만, 매핑 병합은 **얕은 복사**처럼 동작한다. 중첩된 매핑은 공유될 수 있다 — 파서별로 다름.

**함정 3**: 앵커는 **같은 문서 안에서만** 유효하다. 다른 파일에서 참조 못 함.

## 10.8 실전 — Docker Compose 예제

```yaml
x-common: &common
  restart: unless-stopped
  networks:
    - app-net
  logging:
    driver: json-file
    options:
      max-size: "10m"

services:
  web:
    <<: *common
    image: nginx:latest
    ports: ["80:80"]
  api:
    <<: *common
    image: api:latest
    ports: ["8080:8080"]
  worker:
    <<: *common
    image: worker:latest
```

`x-` 접두사 키는 Docker Compose가 무시(**확장 필드**)한다. 앵커 정의 전용으로 좋다.

---

# 11. 태그와 명시적 타입

YAML은 모호한 값에 **태그**로 타입을 명시할 수 있다.

## 11.1 기본 태그

```yaml
a: !!str 42        # "42" (문자열)
b: !!int "42"      # 42 (정수)
c: !!float 1       # 1.0 (실수)
d: !!bool "yes"    # true
e: !!null "ignored"# null
f: !!seq [1, 2, 3]
g: !!map {a: 1}
```

`!!`는 YAML 표준 네임스페이스를 의미.

## 11.2 언제 쓰나

99% 안 쓴다. 자동 추론으로 충분하다. 다음 같은 경우 외에는.

```yaml
# 경계가 모호 — 명시
zip: !!str 06234   # "06234"

# 또는 그냥 따옴표
zip: "06234"
```

따옴표가 더 흔하고 가독성도 좋다.

## 11.3 사용자 정의 태그

직렬화 라이브러리가 만든 객체.

```yaml
person: !Person
  name: Alice
  age: 30
```

PyYAML은 이런 태그를 **클래스로 역직렬화**할 수 있다 — `!!python/object:` 같은 태그로. 이게 보안 문제의 진원지다(24장 참고).

## 11.4 SafeLoader vs Loader

PyYAML 기본 `yaml.load()`는 **모든 태그를 신뢰**한다 — 위험.

```python
import yaml

# 위험 — 임의 코드 실행 가능
yaml.load(untrusted)

# 안전 — 표준 태그만
yaml.safe_load(untrusted)
```

24장에서 자세히.

---

# 12. 다중 문서

한 파일에 여러 YAML 문서를 담을 수 있다.

## 12.1 문법

```yaml
---
name: Alice
age: 30
---
name: Bob
age: 25
---
name: Carol
age: 35
```

`---`(세 하이픈)이 문서 구분. `...`(세 점)으로 끝낼 수도 있다.

```yaml
---
name: Alice
...
---
name: Bob
...
```

`...`는 거의 안 쓴다. `---`만 알면 된다.

## 12.2 시작 마커

`---`는 **첫 문서의 시작**을 알리는 데도 쓰인다.

```yaml
---
name: Alice
```

명시적이라 좋다. 단일 문서에선 생략 가능.

## 12.3 Kubernetes에서

쿠버네티스에서 가장 흔하게 본다. 한 파일에 여러 리소스.

```yaml
---
apiVersion: v1
kind: Service
metadata:
  name: my-svc
spec:
  selector:
    app: my-app
  ports:
    - port: 80
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: my-app
  template:
    metadata:
      labels:
        app: my-app
    spec:
      containers:
        - name: app
          image: nginx
```

`kubectl apply -f file.yaml`로 한 번에 적용.

## 12.4 파싱

PyYAML로:

```python
import yaml

with open('multi.yaml') as f:
    docs = list(yaml.safe_load_all(f))

print(len(docs))     # 3
print(docs[0])       # {'name': 'Alice', 'age': 30}
```

`yq`로:

```bash
# 모든 문서를 JSON 배열로
yq -o=json -I=0 'split_doc' multi.yaml

# 첫 번째 문서만
yq 'select(documentIndex == 0)' multi.yaml
```

## 12.5 디렉티브

`%` 시작 줄은 디렉티브.

```yaml
%YAML 1.2
---
name: Alice
```

YAML 버전 명시. 거의 안 쓴다.

```yaml
%TAG ! tag:example.com,2024:
---
person: !person
  name: Alice
```

태그 단축어. 정말 안 쓴다.

---

# 13. YAML과 JSON

## 13.1 JSON은 YAML의 부분집합

YAML 1.2부터 **모든 JSON은 유효한 YAML**이다.

```yaml
{"name": "Alice", "age": 30, "hobbies": ["reading", "cycling"]}
```

이게 그대로 YAML이다.

## 13.2 차이점

| 항목 | JSON | YAML |
|------|------|------|
| 주석 | 없음 | `#` |
| 따옴표 | 필수 | 대부분 선택 |
| 후행 콤마 | 금지 | 흐름 안에선 허용 |
| 다중 문서 | 안 됨 | `---`로 가능 |
| 참조 | 없음 | 앵커/별칭 |
| 키 타입 | 문자열만 | 임의 |
| 데이터 모델 | 트리 | 그래프 |
| 사람 친화도 | 보통 | 높음 |
| 기계 친화도 | 매우 높음 | 보통 |

## 13.3 변환

JSON → YAML:

```bash
echo '{"name":"Alice","age":30}' | yq -P
# name: Alice
# age: 30
```

YAML → JSON:

```bash
yq -o=json file.yaml
```

Python으로:

```python
import yaml, json

# JSON → YAML
data = json.loads(json_str)
yaml_str = yaml.safe_dump(data, default_flow_style=False)

# YAML → JSON
data = yaml.safe_load(yaml_str)
json_str = json.dumps(data, indent=2)
```

## 13.4 언제 어느 쪽?

- **API 페이로드, 머신 간 통신** → JSON
- **사람이 편집하는 설정** → YAML
- **로그, 데이터 파이프라인** → JSON 또는 JSONL
- **OpenAPI 스펙** → 둘 다 (사람은 YAML, CI는 JSON)

## 13.5 YAML로 JSON 쓰기

YAML이 JSON 상위집합이라는 점을 활용해, "**JSON 형식으로 YAML을 쓰면**" 둘 다 만족한다.

```yaml
{
  "name": "Alice",
  "age": 30
}
```

엄밀한 스키마 검증을 거치는 도구에는 이게 안전할 때가 있다.

---

# 14. YAML 1.1 vs 1.2 — 함정

YAML 1.1과 1.2는 **호환되지 않는다**. 거의 모든 함정이 여기서 나온다.

## 14.1 어느 버전을 쓰나

| 도구 | YAML 버전 |
|------|----------|
| PyYAML | 1.1 |
| ruamel.yaml | 1.2 (선택) |
| Go (yaml.v3) | 1.2 |
| JS (js-yaml) | 1.2 (기본) |
| Kubernetes | 1.1 |
| Helm | 1.2 |
| Ansible | 1.1 |

뭘 쓰는지 모르면 **1.1을 가정하고 보수적으로** 쓴다.

## 14.2 노르웨이 문제

YAML 1.1에서:

```yaml
- yes
- no
- on
- off
- y
- n
- True
- TRUE
- Yes
- NO
```

이 모두가 **불리언**이다. YAML 1.2에서는 `true`/`True`/`TRUE`/`false`/`False`/`FALSE`만 불리언, 나머지는 문자열.

해결:

```yaml
countries:
  - "NO"     # 노르웨이
  - "FR"
  - "DE"
```

## 14.3 8진수 함정

YAML 1.1: `0`으로 시작하는 정수는 8진수.

```yaml
zip: 06234     # 1.1: 8진수 → 3228 (또는 에러)
               # 1.2: 그냥 숫자 6234 (또는 문자열 — 구현 의존)
```

해결:

```yaml
zip: "06234"
```

## 14.4 문자열 보이는 숫자

```yaml
version: 1.10        # 실수 1.1 (마지막 0 손실)
version: "1.10"      # 문자열 그대로
```

소프트웨어 버전, 전화번호, 우편번호, 카드번호는 **항상 따옴표**.

## 14.5 시간 형식

YAML 1.1:

```yaml
time: 12:30          # 60진수 → 12*60+30 = 750
time: 1:23:45        # 60진수 → 1*3600+23*60+45 = 5025
```

문자가 콜론을 포함하면 60진수로 해석할 수 있다. **항상 따옴표**.

```yaml
time: "12:30"
```

## 14.6 Sexagesimal — 60진수

YAML 1.1에서 `:`로 구분된 숫자는 60진수.

```yaml
a: 1:30           # 90 (1*60+30)
b: 1:30:00        # 5400 (1*3600+30*60+0)
```

YAML 1.2에서 제거됐지만, 1.1 파서는 여전히 그렇게 해석한다.

## 14.7 안전 규칙 — 따옴표를 치는 경우

다음 값들은 **항상 따옴표**:

1. 두 글자 국가코드 (`"NO"`, `"GB"`)
2. 0으로 시작하는 숫자 (`"06234"`)
3. 콜론 포함 (`"12:30"`)
4. 버전 문자열 (`"1.10"`)
5. yes/no/on/off/y/n으로 보이는 단어
6. true/false로 보이는 단어
7. null/None/Null
8. 숫자로만 이루어진 문자열 (`"42"`)
9. 이메일 (`"a@b.com"`은 안전하지만 명시 권장)

기억하기 어렵다면 **모든 값에 따옴표** — 안전하지만 가독성 저하. 균형을 잡자.

---

# 15. 실전 — Docker Compose

## 15.1 기본 구조

```yaml
# docker-compose.yml
version: "3.9"

services:
  web:
    image: nginx:latest
    ports:
      - "80:80"

  db:
    image: postgres:15
    environment:
      POSTGRES_PASSWORD: secret
    volumes:
      - db_data:/var/lib/postgresql/data

volumes:
  db_data:
```

## 15.2 다양한 표기

ports는 두 가지 방식.

```yaml
# 단순 — 흐름 스타일
ports:
  - "80:80"
  - "443:443"

# 자세히 — 매핑 스타일
ports:
  - target: 80
    published: 80
    protocol: tcp
    mode: host
```

## 15.3 environment

세 가지 표기.

```yaml
# 매핑
environment:
  DB_HOST: db
  DB_PORT: 5432

# 시퀀스 — KEY=VALUE
environment:
  - DB_HOST=db
  - DB_PORT=5432

# .env 파일 참조
env_file:
  - .env
```

## 15.4 환경변수 보간

```yaml
services:
  web:
    image: nginx:${NGINX_VERSION:-latest}
    ports:
      - "${WEB_PORT}:80"
```

`${VAR}` 또는 `$VAR`. `${VAR:-default}`로 기본값.

## 15.5 앵커로 중복 제거

```yaml
x-restart: &restart
  restart: unless-stopped

x-logging: &logging
  logging:
    driver: json-file
    options:
      max-size: "10m"
      max-file: "5"

services:
  web:
    <<: [*restart, *logging]
    image: nginx
  api:
    <<: [*restart, *logging]
    image: api:latest
  worker:
    <<: [*restart, *logging]
    image: worker:latest
```

## 15.6 의존성

```yaml
services:
  api:
    image: api:latest
    depends_on:
      - db
      - redis
    # 또는 자세히
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started
```

## 15.7 헬스체크

```yaml
services:
  db:
    image: postgres:15
    healthcheck:
      test: ["CMD", "pg_isready", "-U", "postgres"]
      interval: 10s
      timeout: 5s
      retries: 5
```

## 15.8 네트워크와 볼륨

```yaml
services:
  web:
    networks:
      - frontend
      - backend
    volumes:
      - ./html:/usr/share/nginx/html
      - cache:/var/cache/nginx

networks:
  frontend:
  backend:
    driver: bridge

volumes:
  cache:
    driver: local
```

## 15.9 멀티 환경 — override 파일

기본:

```yaml
# docker-compose.yml
services:
  web:
    image: myapp:latest
    environment:
      ENV: production
```

개발 오버라이드:

```yaml
# docker-compose.override.yml
services:
  web:
    environment:
      ENV: development
    volumes:
      - ./src:/app/src
```

`docker-compose up`은 두 파일을 자동 머지. `docker-compose -f a.yml -f b.yml`로 명시 가능.

## 15.10 전체 예제

```yaml
version: "3.9"

x-app-defaults: &app-defaults
  restart: unless-stopped
  networks:
    - app-net
  logging:
    driver: json-file
    options:
      max-size: "10m"

services:
  web:
    <<: *app-defaults
    image: nginx:1.25
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - api

  api:
    <<: *app-defaults
    image: myapi:${TAG:-latest}
    environment:
      DATABASE_URL: postgres://app:${DB_PASSWORD}@db:5432/app
      REDIS_URL: redis://redis:6379/0
    healthcheck:
      test: ["CMD", "wget", "--quiet", "--spider", "http://localhost:8080/health"]
      interval: 30s
      timeout: 5s
      retries: 3
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started

  db:
    <<: *app-defaults
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: app
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: app
    volumes:
      - db_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD", "pg_isready", "-U", "app"]
      interval: 10s

  redis:
    <<: *app-defaults
    image: redis:7-alpine
    volumes:
      - redis_data:/data

networks:
  app-net:

volumes:
  db_data:
  redis_data:
```

---

# 16. 실전 — Kubernetes

## 16.1 모든 매니페스트의 4요소

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: my-pod
spec:
  containers:
    - name: app
      image: nginx
```

- `apiVersion` — 어느 API
- `kind` — 어떤 리소스
- `metadata` — 이름, 네임스페이스, 라벨, 어노테이션
- `spec` — 원하는 상태

## 16.2 Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
  labels:
    app: web
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web
  template:
    metadata:
      labels:
        app: web
    spec:
      containers:
        - name: nginx
          image: nginx:1.25
          ports:
            - containerPort: 80
          resources:
            requests:
              cpu: 100m
              memory: 128Mi
            limits:
              cpu: 500m
              memory: 512Mi
```

## 16.3 Service

```yaml
apiVersion: v1
kind: Service
metadata:
  name: web
spec:
  type: ClusterIP
  selector:
    app: web
  ports:
    - port: 80
      targetPort: 80
      protocol: TCP
```

## 16.4 ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  database_url: "postgres://db:5432/app"
  log_level: "info"
  config.yaml: |
    server:
      host: 0.0.0.0
      port: 8080
    cache:
      ttl: 300
```

`|`로 멀티라인 설정 파일을 그대로 임베드.

## 16.5 Secret

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: db-secret
type: Opaque
stringData:
  username: admin
  password: super-secret
```

`stringData`는 평문, `data`는 base64 인코딩 필수.

## 16.6 환경변수 주입

```yaml
spec:
  containers:
    - name: app
      image: myapp
      env:
        - name: ENV
          value: production
        - name: DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: password
      envFrom:
        - configMapRef:
            name: app-config
```

## 16.7 볼륨 마운트

```yaml
spec:
  volumes:
    - name: config
      configMap:
        name: app-config
    - name: data
      persistentVolumeClaim:
        claimName: data-pvc
  containers:
    - name: app
      image: myapp
      volumeMounts:
        - name: config
          mountPath: /etc/app
        - name: data
          mountPath: /var/lib/app
```

## 16.8 Probe

```yaml
spec:
  containers:
    - name: app
      image: myapp
      livenessProbe:
        httpGet:
          path: /healthz
          port: 8080
        initialDelaySeconds: 30
        periodSeconds: 10
      readinessProbe:
        httpGet:
          path: /ready
          port: 8080
        initialDelaySeconds: 5
        periodSeconds: 5
```

## 16.9 라벨과 셀렉터

```yaml
metadata:
  labels:
    app: web
    tier: frontend
    env: prod
    version: "1.10"     # 따옴표! 1.10 → 1.1 함정
```

셀렉터로 매칭:

```yaml
spec:
  selector:
    matchLabels:
      app: web
      tier: frontend
```

## 16.10 다중 리소스 한 파일

```yaml
---
apiVersion: v1
kind: Namespace
metadata:
  name: my-app
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
  namespace: my-app
data:
  log_level: info
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
  namespace: my-app
spec:
  # ...
```

## 16.11 Helm 템플릿

Helm은 YAML 위에 **Go 템플릿**을 얹는다.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ .Values.appName }}
spec:
  replicas: {{ .Values.replicas | default 1 }}
  template:
    spec:
      containers:
        - name: app
          image: {{ .Values.image.repository }}:{{ .Values.image.tag }}
          {{- if .Values.env }}
          env:
          {{- range $k, $v := .Values.env }}
            - name: {{ $k }}
              value: {{ $v | quote }}
          {{- end }}
          {{- end }}
```

`{{ }}`는 템플릿 변수, `{{- }}`는 앞뒤 공백 제거. 렌더링 후가 진짜 YAML이다.

## 16.12 자주 하는 실수

**실수 1**: 버전을 따옴표 없이

```yaml
image: nginx:1.10    # OK (image는 문자열로 인식)
labels:
  version: 1.10      # 잘못 — 1.1로 변환
  version: "1.10"    # 올바름
```

**실수 2**: replicas를 문자열로

```yaml
replicas: "3"        # 잘못 — int여야 함
replicas: 3
```

**실수 3**: bool

```yaml
allowPrivilegeEscalation: "false"   # 잘못 — 문자열
allowPrivilegeEscalation: false     # 올바름
```

---

# 17. 실전 — GitHub Actions

## 17.1 기본 구조

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main]
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - run: npm ci
      - run: npm test
```

## 17.2 트리거

```yaml
on:
  # 푸시
  push:
    branches: [main, develop]
    paths:
      - 'src/**'
      - 'package.json'

  # PR
  pull_request:
    types: [opened, synchronize]

  # 스케줄 (cron)
  schedule:
    - cron: '0 0 * * *'   # 매일 자정 UTC

  # 수동
  workflow_dispatch:
    inputs:
      env:
        description: 'Environment'
        required: true
        type: choice
        options: [staging, prod]
```

## 17.3 매트릭스 빌드

```yaml
jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        node: [18, 20, 22]
        exclude:
          - os: macos-latest
            node: 18
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node }}
      - run: npm test
```

## 17.4 환경변수와 시크릿

```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    env:
      NODE_ENV: production
    steps:
      - run: ./deploy.sh
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          API_TOKEN: ${{ secrets.API_TOKEN }}
```

## 17.5 조건부 실행

```yaml
jobs:
  deploy:
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - run: ./deploy.sh

      - name: Notify on failure
        if: failure()
        run: ./notify.sh

      - name: Cleanup
        if: always()
        run: ./cleanup.sh
```

## 17.6 잡 의존성

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - run: npm test

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - run: npm run build

  deploy:
    needs: [test, build]
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - run: ./deploy.sh
```

## 17.7 멀티라인 스크립트

```yaml
- name: Deploy
  run: |
    set -euo pipefail
    echo "Deploying to ${{ inputs.env }}..."
    aws s3 sync ./dist s3://my-bucket
    aws cloudfront create-invalidation --distribution-id ABC --paths '/*'
    echo "Done."
```

## 17.8 출력값 공유

```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    outputs:
      version: ${{ steps.ver.outputs.version }}
    steps:
      - id: ver
        run: echo "version=$(cat VERSION)" >> $GITHUB_OUTPUT

  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - run: echo "Deploying ${{ needs.build.outputs.version }}"
```

## 17.9 재사용 워크플로

```yaml
# .github/workflows/reusable.yml
name: Reusable Test

on:
  workflow_call:
    inputs:
      node-version:
        type: string
        default: '20'

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ inputs.node-version }}
      - run: npm test
```

호출 측:

```yaml
jobs:
  test:
    uses: ./.github/workflows/reusable.yml
    with:
      node-version: '22'
```

## 17.10 GitHub Actions의 YAML 함정

**병합 키 미지원**:

```yaml
# 안 통함
defaults: &defaults
  runs-on: ubuntu-latest

jobs:
  test:
    <<: *defaults
```

대안 — `defaults` 키나 재사용 워크플로 활용.

```yaml
defaults:
  run:
    shell: bash
    working-directory: ./app
```

**표현식 따옴표**:

```yaml
# 잘못 — 콜론이 매핑으로 해석
if: github.event.label.name == 'bug'

# 올바름 (예방적 따옴표)
if: ${{ github.event.label.name == 'bug' }}
```

---

# 18. 실전 — Ansible

## 18.1 플레이북 기본

```yaml
---
- name: Configure web servers
  hosts: webservers
  become: yes
  tasks:
    - name: Install nginx
      apt:
        name: nginx
        state: present

    - name: Start nginx
      service:
        name: nginx
        state: started
        enabled: yes
```

## 18.2 변수

```yaml
- name: Configure
  hosts: all
  vars:
    nginx_port: 8080
    nginx_user: www-data

  tasks:
    - name: Configure
      template:
        src: nginx.conf.j2
        dest: /etc/nginx/nginx.conf
      vars:
        max_connections: 1024
```

`vars/`, `defaults/`, `host_vars/`, `group_vars/` — 다양한 변수 위치.

## 18.3 핸들러

```yaml
- hosts: webservers
  tasks:
    - name: Update config
      template:
        src: nginx.conf.j2
        dest: /etc/nginx/nginx.conf
      notify: restart nginx

  handlers:
    - name: restart nginx
      service:
        name: nginx
        state: restarted
```

## 18.4 반복

```yaml
tasks:
  - name: Install packages
    apt:
      name: "{{ item }}"
      state: present
    loop:
      - nginx
      - postgresql
      - redis

  - name: Create users
    user:
      name: "{{ item.name }}"
      groups: "{{ item.groups }}"
    loop:
      - { name: alice, groups: admin }
      - { name: bob, groups: users }
```

## 18.5 조건

```yaml
- name: Install nginx
  apt:
    name: nginx
  when: ansible_os_family == "Debian"

- name: Install on RHEL
  yum:
    name: nginx
  when:
    - ansible_os_family == "RedHat"
    - ansible_distribution_major_version == "8"
```

## 18.6 인벤토리

```yaml
# inventory.yml
all:
  children:
    webservers:
      hosts:
        web1.example.com:
        web2.example.com:
      vars:
        http_port: 80

    dbservers:
      hosts:
        db1.example.com:
          db_role: primary
        db2.example.com:
          db_role: replica
```

## 18.7 롤

```yaml
- hosts: webservers
  roles:
    - common
    - nginx
    - { role: app, app_version: "1.10" }
```

## 18.8 Ansible의 YAML 특이점

- 1.1 파서 (PyYAML)
- 노르웨이 문제 정통 — `state: yes`는 동작하지만 변수 값으로는 위험
- Jinja2 템플릿이 YAML과 섞임 — `"{{ var }}"` 따옴표 권장

---

# 19. 실전 — CI/CD 일반

## 19.1 GitLab CI

```yaml
stages:
  - test
  - build
  - deploy

variables:
  NODE_ENV: production

.before_script: &node-setup
  before_script:
    - npm ci

test:
  stage: test
  image: node:20
  <<: *node-setup
  script:
    - npm test
  coverage: '/Coverage: \d+\.\d+%/'

build:
  stage: build
  image: node:20
  <<: *node-setup
  script:
    - npm run build
  artifacts:
    paths:
      - dist/

deploy:
  stage: deploy
  image: alpine
  script:
    - ./deploy.sh
  only:
    - main
```

GitLab CI는 **병합 키를 지원**한다.

## 19.2 CircleCI

```yaml
version: 2.1

executors:
  node:
    docker:
      - image: cimg/node:20.0

jobs:
  test:
    executor: node
    steps:
      - checkout
      - run: npm ci
      - run: npm test

workflows:
  build-test:
    jobs:
      - test
```

## 19.3 Travis CI

```yaml
language: node_js
node_js:
  - "20"

cache:
  npm: true

script:
  - npm test

deploy:
  provider: heroku
  api_key: $HEROKU_API_KEY
  app: my-app
  on:
    branch: main
```

---

# 20. 실전 — 설정 파일

## 20.1 OpenAPI

```yaml
openapi: 3.0.0
info:
  title: My API
  version: "1.0.0"

paths:
  /users/{id}:
    get:
      summary: Get user
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: integer
      responses:
        '200':
          description: OK
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/User'

components:
  schemas:
    User:
      type: object
      properties:
        id:
          type: integer
        name:
          type: string
      required:
        - id
        - name
```

## 20.2 Prometheus

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: prometheus
    static_configs:
      - targets: ['localhost:9090']

  - job_name: app
    metrics_path: /metrics
    static_configs:
      - targets:
          - 'app1:8080'
          - 'app2:8080'

rule_files:
  - 'rules/*.yml'
```

## 20.3 Grafana 데이터소스

```yaml
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true

  - name: Loki
    type: loki
    access: proxy
    url: http://loki:3100
```

## 20.4 yamllint 자체 설정

```yaml
# .yamllint
extends: default

rules:
  line-length:
    max: 120
  comments:
    min-spaces-from-content: 1
  indentation:
    spaces: 2
    indent-sequences: true
```

## 20.5 pre-commit hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files

  - repo: https://github.com/adrienverge/yamllint
    rev: v1.33.0
    hooks:
      - id: yamllint
```

---

# 21. 도구 — yq

`yq`는 **YAML용 jq**다. 두 구현이 있다.

- **Go yq** (mikefarah/yq) — 가장 인기, jq 비슷한 문법
- **Python yq** (kislyuk/yq) — jq 그대로 사용

여기선 **Go yq** 기준.

## 21.1 설치

```bash
# Linux
sudo wget -qO /usr/local/bin/yq https://github.com/mikefarah/yq/releases/latest/download/yq_linux_amd64
sudo chmod +x /usr/local/bin/yq

# macOS
brew install yq

# 버전 확인
yq --version
```

## 21.2 기본 — 읽기

```bash
# 전체
yq '.' file.yaml

# 특정 경로
yq '.spec.replicas' deployment.yaml

# 출력 형식
yq -o=json '.' file.yaml      # JSON
yq -o=yaml '.' file.yaml      # YAML (기본)
yq -o=props '.' file.yaml     # 프로퍼티
yq -o=xml '.' file.yaml       # XML
```

## 21.3 필터링

```bash
# 시퀀스의 모든 요소
yq '.servers[]' file.yaml

# 인덱스
yq '.servers[0]' file.yaml

# 키-값
yq '.servers[].name' file.yaml

# 조건
yq '.servers[] | select(.tier == "prod")' file.yaml
```

## 21.4 수정

```bash
# 인플레이스 수정
yq -i '.spec.replicas = 5' deployment.yaml

# 새 필드 추가
yq -i '.metadata.labels.env = "prod"' deployment.yaml

# 삭제
yq -i 'del(.metadata.labels.tmp)' deployment.yaml

# 환경변수 사용
yq -i '.image.tag = strenv(TAG)' values.yaml
```

## 21.5 다중 문서

```bash
# 모든 문서
yq '.' multi.yaml

# 특정 문서만
yq 'select(documentIndex == 0)' multi.yaml

# kind로 필터
yq 'select(.kind == "Deployment")' k8s.yaml
```

## 21.6 머지

```bash
# 두 파일 머지 (오른쪽 우선)
yq '. *= load("override.yaml")' base.yaml

# 또는
yq eval-all 'select(fileIndex == 0) * select(fileIndex == 1)' a.yaml b.yaml
```

## 21.7 변환

```bash
# YAML → JSON
yq -o=json file.yaml > file.json

# JSON → YAML
yq -P file.json > file.yaml

# 또는 stdin
cat file.json | yq -P
```

## 21.8 실전 레시피

```bash
# 모든 컨테이너 이미지 추출
yq '.. | select(has("image")) | .image' k8s.yaml | sort -u

# replicas 모두 0으로
yq -i '(.. | select(has("replicas"))) .replicas = 0' k8s.yaml

# 여러 파일에서 같은 필드 변경
for f in *.yaml; do
  yq -i '.metadata.namespace = "production"' "$f"
done
```

## 21.9 Helm values 수정

```bash
yq -i '.image.tag = strenv(TAG) | .replicaCount = 5' values.yaml
```

---

# 22. 도구 — yamllint

YAML 문법/스타일 린터.

## 22.1 설치

```bash
pip install yamllint
# 또는
sudo apt install yamllint
```

## 22.2 기본 사용

```bash
# 한 파일
yamllint file.yaml

# 디렉토리
yamllint .

# 규칙 강도
yamllint --strict .
```

## 22.3 설정 파일

`.yamllint`(루트) 또는 `~/.config/yamllint/config`:

```yaml
extends: default

rules:
  # 줄 길이
  line-length:
    max: 120
    level: warning

  # 들여쓰기
  indentation:
    spaces: 2
    indent-sequences: true
    check-multi-line-strings: false

  # 주석
  comments:
    require-starting-space: true
    min-spaces-from-content: 1

  # 중복 키
  key-duplicates: enable

  # 따옴표 일관성
  quoted-strings:
    quote-type: any
    required: only-when-needed

  # 불리언 체크 — 노르웨이 문제 방지
  truthy:
    allowed-values: ['true', 'false']
```

## 22.4 인라인 비활성화

```yaml
# yamllint disable-line rule:line-length
extremely_long_key_that_exceeds_the_line_length_limit_of_120_characters: short_value

# yamllint disable rule:indentation
weird:
   indent: 3-spaces
# yamllint enable
```

## 22.5 사전 설정

```bash
# default
yamllint -c "default" file.yaml

# relaxed (덜 엄격)
yamllint -c "relaxed" file.yaml
```

## 22.6 CI 통합

```yaml
# .github/workflows/lint.yml
name: Lint

on: [push, pull_request]

jobs:
  yamllint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - run: pip install yamllint
      - run: yamllint .
```

---

# 23. 도구 — 언어별 라이브러리

## 23.1 Python — PyYAML

```python
import yaml

# 읽기
with open('config.yaml') as f:
    config = yaml.safe_load(f)

# 쓰기
data = {'name': 'Alice', 'hobbies': ['reading', 'cycling']}
with open('out.yaml', 'w') as f:
    yaml.safe_dump(data, f, default_flow_style=False)

# 다중 문서
with open('multi.yaml') as f:
    docs = list(yaml.safe_load_all(f))

# 한 번에 여러 문서
with open('out.yaml', 'w') as f:
    yaml.safe_dump_all([{'a': 1}, {'b': 2}], f)
```

`yaml.load`는 **위험**. 항상 `safe_load`.

## 23.2 Python — ruamel.yaml

PyYAML의 한계(주석 손실, YAML 1.2 미지원)를 보완.

```python
from ruamel.yaml import YAML

yaml = YAML()
yaml.preserve_quotes = True   # 따옴표 보존
yaml.indent(mapping=2, sequence=4, offset=2)

# 읽기 — 주석도 보존됨
with open('config.yaml') as f:
    data = yaml.load(f)

data['version'] = '2.0'

# 쓰기 — 주석/따옴표 그대로
with open('config.yaml', 'w') as f:
    yaml.dump(data, f)
```

도구로 YAML을 수정할 때 가장 안전한 라이브러리.

## 23.3 Go — yaml.v3

```go
package main

import (
    "fmt"
    "os"
    "gopkg.in/yaml.v3"
)

type Config struct {
    Name    string   `yaml:"name"`
    Hobbies []string `yaml:"hobbies"`
}

func main() {
    data, _ := os.ReadFile("config.yaml")

    var cfg Config
    yaml.Unmarshal(data, &cfg)

    fmt.Println(cfg.Name)

    out, _ := yaml.Marshal(&cfg)
    os.WriteFile("out.yaml", out, 0644)
}
```

태그로 필드명 매핑. `yaml:"name,omitempty"`로 빈 값 생략.

## 23.4 JavaScript — js-yaml

```javascript
const yaml = require('js-yaml');
const fs = require('fs');

// 읽기
const data = yaml.load(fs.readFileSync('config.yaml', 'utf8'));

// 쓰기
fs.writeFileSync('out.yaml', yaml.dump({name: 'Alice'}));

// 안전 모드 (기본)
yaml.load(input);  // SafeLoad와 동일

// 다중 문서
yaml.loadAll(text, doc => console.log(doc));
```

## 23.5 Rust — serde_yaml

```rust
use serde::{Deserialize, Serialize};

#[derive(Serialize, Deserialize)]
struct Config {
    name: String,
    hobbies: Vec<String>,
}

let yaml = std::fs::read_to_string("config.yaml")?;
let cfg: Config = serde_yaml::from_str(&yaml)?;

let out = serde_yaml::to_string(&cfg)?;
```

## 23.6 Java — SnakeYAML

```java
import org.yaml.snakeyaml.Yaml;

Yaml yaml = new Yaml();
Map<String, Object> data = yaml.load(new FileInputStream("config.yaml"));

String out = yaml.dump(data);
```

## 23.7 Ruby

```ruby
require 'yaml'

data = YAML.load_file('config.yaml')
File.write('out.yaml', data.to_yaml)
```

`YAML.load`는 안전(Ruby 3.1+ 기본). 그 전 버전은 `YAML.safe_load`.

---

# 24. 보안과 함정

## 24.1 PyYAML `yaml.load` 취약점

YAML 태그로 임의 코드 실행 가능.

```yaml
# malicious.yaml
!!python/object/apply:os.system ["rm -rf /"]
```

```python
import yaml
yaml.load(open('malicious.yaml'))   # 위험! 실제 실행됨
yaml.safe_load(open('malicious.yaml'))   # 안전 — 거부
```

**규칙**: 신뢰할 수 없는 입력은 **언제나** `safe_load`.

## 24.2 Billion Laughs (YAML 폭탄)

```yaml
a: &a ["lol","lol","lol","lol","lol","lol","lol","lol","lol"]
b: &b [*a,*a,*a,*a,*a,*a,*a,*a,*a]
c: &c [*b,*b,*b,*b,*b,*b,*b,*b,*b]
d: &d [*c,*c,*c,*c,*c,*c,*c,*c,*c]
```

깊이 4에 9^4 = 6561개. 깊이 9면 수십억. 메모리 폭발.

방어: 신뢰할 수 없는 입력에 **크기/깊이 제한**.

## 24.3 키 충돌

```yaml
admin: alice
admin: eve    # 후자 승리
```

대부분의 파서가 마지막 값을 채택. 의도적 공격 가능 — 사람은 첫 줄만 보고 안전하다고 믿을 수 있음.

방어: yamllint `key-duplicates: enable`로 검출.

## 24.4 시크릿 노출

```yaml
# 절대 커밋하지 말 것
database:
  password: super-secret-password
  api_key: sk-12345
```

대신:

```yaml
database:
  password: ${DB_PASSWORD}
  api_key: ${API_KEY}
```

또는 시크릿 매니저 (Vault, AWS Secrets Manager, K8s Secret).

## 24.5 들여쓰기 파싱 차이

```yaml
key:
  - item1
   - item2    # 1칸 더
```

PyYAML과 ruamel.yaml의 동작이 다를 수 있다. 항상 yamllint 검증.

## 24.6 파서별 차이 — `version`

```yaml
version: 1.0
```

- PyYAML: `1.0` (float)
- ruamel: `1.0` (float, 그러나 LiteralFloat — 표시 보존)
- yaml.v3 (Go): `"1.0"` (string)

`version`처럼 의미 있는 필드는 **항상 따옴표**.

## 24.7 BOM 문자

UTF-8 BOM(EF BB BF)이 파일 앞에 붙으면 일부 파서가 실패.

```bash
# BOM 검출
head -c 3 file.yaml | xxd

# BOM 제거
sed -i '1s/^\xEF\xBB\xBF//' file.yaml
```

## 24.8 줄바꿈 형식

CRLF(윈도우) vs LF(유닉스). 대부분 파서는 둘 다 처리하지만, **블록 스칼라**에서는 다를 수 있다.

```bash
# 변환
dos2unix file.yaml
```

## 24.9 인코딩

YAML은 **UTF-8**이 기본. UTF-16, UTF-32도 명세에 있지만 거의 안 씀. ANSI/EUC-KR로 저장하지 말자.

---

# 25. 모범 사례

## 25.1 일관성

- 들여쓰기 칸 수 통일 (보통 2)
- 시퀀스 들여쓰기 스타일 통일
- 따옴표 정책 통일 (필요할 때만 등)

## 25.2 따옴표 — 보수적으로

쓰지 않으면 가독성↑, 쓰지 않으면 함정↑. 균형:

- 문자열로 보장하고 싶은 값 → 따옴표
- 단순 단어, 명확한 숫자 → 따옴표 없음

## 25.3 키 정렬

가능한 한 **알파벳 순**. 또는 **의미 그룹 + 알파벳**:

```yaml
# 메타데이터 먼저
name: my-app
version: "1.10"
description: ...

# 그 다음 의미 그룹
network:
  host: ...
  port: ...
storage:
  driver: ...
  path: ...
```

## 25.4 환경 분리

```yaml
# config.base.yaml
log_level: info
timeout: 30

# config.prod.yaml
log_level: warn

# config.dev.yaml
log_level: debug
```

머지: `yq '. *= load("prod.yaml")' base.yaml`.

## 25.5 검증

CI에서 항상 yamllint + 스키마 검증.

```bash
# 스키마 검증
yajsv -s schema.json file.yaml

# Kubernetes 매니페스트
kubeval *.yaml
kubeconform *.yaml
```

## 25.6 변경 이력

YAML 자체는 주석을 보존하지 않으므로 (도구로 다시 쓰면 사라짐), 변경 이력은 **git log**.

## 25.7 큰 파일 쪼개기

500줄 넘으면 분할.

```yaml
# main.yaml
imports:
  - servers.yaml
  - networks.yaml
  - volumes.yaml
```

YAML 자체는 import가 없다 — 도구가 처리(Helm `_helpers.tpl`, Ansible `include_vars`).

## 25.8 디폴트 + 오버라이드

```yaml
defaults: &defaults
  timeout: 30
  retries: 3
  log_level: info

production:
  <<: *defaults
  log_level: warn

development:
  <<: *defaults
  log_level: debug
  timeout: 300
```

## 25.9 매직 넘버 명시

```yaml
# 나쁨
retry_count: 5
timeout: 30000

# 좋음
retry_count: 5  # 1xx/5xx 응답 시 최대 재시도
timeout: 30000  # ms (30초)
```

## 25.10 시크릿은 따로

```yaml
# config.yaml
database:
  host: db.local
  user: app
  password: !env DB_PASSWORD   # 또는 ${DB_PASSWORD}
```

`.env`, Vault, K8s Secret. 절대 인라인 금지.

## 25.11 안티패턴

**과도한 앵커 사용** — 가독성 떨어짐:

```yaml
# 너무 많은 참조
a: &a 1
b: &b *a
c: &c [*a, *b]
d: &d {x: *a, y: *b, z: *c}
e: &e [*a, *b, *c, *d]
```

3단계 이상 깊이는 자제.

**무의미한 흐름 스타일**:

```yaml
# 나쁨 — 가독성 저하
config: {server: {host: "...", port: 80, tls: {cert: "...", key: "..."}}}

# 좋음
config:
  server:
    host: ...
    port: 80
    tls:
      cert: ...
      key: ...
```

---

# 26. 부록 — 치트시트

## 26.1 빠른 문법

```yaml
# 주석

# 스칼라
str: hello              # 평범
str: "hello"            # 큰따옴표 (이스케이프 가능)
str: 'hello'            # 작은따옴표 (이스케이프 거의 없음)
int: 42
float: 3.14
bool: true
nul: null               # 또는 ~ 또는 빈 값

# 시퀀스
list:
  - a
  - b
  - c
list2: [a, b, c]

# 매핑
map:
  k1: v1
  k2: v2
map2: {k1: v1, k2: v2}

# 멀티라인 — 개행 보존
literal: |
  line 1
  line 2

# 멀티라인 — 개행 → 공백
folded: >
  long
  line

# 앵커와 별칭
defaults: &d
  x: 1
extends:
  <<: *d
  y: 2

# 다중 문서
---
doc: 1
---
doc: 2
```

## 26.2 항상 따옴표 칠 것

```yaml
# 노르웨이 문제
country: "NO"

# 0으로 시작
zip: "06234"

# 콜론 포함
time: "12:30"

# 버전
version: "1.10"

# 불리언 같은 단어
answer: "yes"

# null 같은 단어
text: "null"
```

## 26.3 Chomp 지시자

| 형식 | 끝 개행 |
|------|---------|
| `\|` | 1개 |
| `\|-` | 0개 |
| `\|+` | 모두 |
| `>` | 1개 |
| `>-` | 0개 |
| `>+` | 모두 |

## 26.4 yq 빠른 참조

```bash
# 읽기
yq '.path.to.field' file.yaml

# 변환
yq -o=json file.yaml
yq -P file.json

# 수정
yq -i '.x.y = 5' file.yaml
yq -i 'del(.x.y)' file.yaml

# 머지
yq '. *= load("override.yaml")' base.yaml

# 다중 문서
yq 'select(.kind == "Deployment")' k8s.yaml
```

## 26.5 yamllint 빠른 참조

```bash
# 검사
yamllint file.yaml
yamllint .

# 강한 모드
yamllint --strict .

# 설정 파일
yamllint -c .yamllint .
```

## 26.6 PyYAML 빠른 참조

```python
import yaml

# 읽기 (안전)
data = yaml.safe_load(open('f.yaml'))

# 쓰기
yaml.safe_dump(data, open('f.yaml', 'w'),
               default_flow_style=False,
               sort_keys=False,
               allow_unicode=True)

# 다중
docs = list(yaml.safe_load_all(open('f.yaml')))
```

## 26.7 자주 쓰는 패턴

**환경별 설정**:

```yaml
defaults: &d
  log: info
  retry: 3

prod:
  <<: *d
  log: warn

dev:
  <<: *d
  log: debug
```

**Compose 공통 설정**:

```yaml
x-common: &common
  restart: unless-stopped
  networks: [app]

services:
  web:
    <<: *common
    image: nginx
```

**K8s 다중 리소스**:

```yaml
---
apiVersion: v1
kind: ConfigMap
# ...
---
apiVersion: apps/v1
kind: Deployment
# ...
```

**GHA 매트릭스**:

```yaml
strategy:
  matrix:
    os: [ubuntu-latest, macos-latest]
    node: [20, 22]
```

## 26.8 디버깅 체크리스트

YAML이 안 읽힐 때:

1. 탭 있나? (`grep -P '\t' file.yaml`)
2. 들여쓰기 일관적인가?
3. 콜론 뒤 공백 있나?
4. 하이픈 뒤 공백 있나?
5. 따옴표 균형 맞나?
6. yamllint 통과하나?
7. `yq '.' file.yaml`로 파싱되나?

값이 이상할 때:

1. 노르웨이 문제? (yes/no/on/off)
2. 8진수 변환? (0으로 시작)
3. 시간으로 해석? (콜론 포함)
4. 버전 잘림? (1.10 → 1.1)
5. 중복 키?
6. 자동 추론 미스?

## 26.9 자주 쓰는 변환

```bash
# YAML → JSON
yq -o=json file.yaml

# JSON → YAML
yq -P file.json

# YAML → 환경변수
yq '.. | select(type == "!!str") | path | join("_") + "=" + .' file.yaml

# YAML → 평탄화
yq '. as $root | paths(scalars) as $p | [$p, getpath($p)]' file.yaml

# 두 YAML 머지
yq eval-all 'select(fileIndex == 0) * select(fileIndex == 1)' a.yaml b.yaml

# 모든 image 추출 (K8s)
yq '.. | select(has("image")) | .image' *.yaml | sort -u
```

## 26.10 마무리

YAML은 **간단해 보이지만 함정이 많다**. 핵심 규칙:

1. **공백만**, 탭 금지
2. **콜론 뒤 공백** 필수
3. **노르웨이 문제** 기억하기 (NO, yes, on…)
4. **버전/우편번호/시간** 따옴표
5. **`safe_load`** 항상
6. **yamllint** CI에 넣기
7. **앵커 + 병합 키**로 중복 제거
8. **다중 문서**는 `---`로
9. **시크릿은 인라인 금지**
10. **잘 모르겠으면 따옴표**

이 열 가지면 99%의 YAML 작업에서 살아남는다.

---

> 끝.
> 작성일: 2026-05-06
> 라이선스: 자유 활용
