# GitHub Actions 기초와 응용
## 실무 자동화를 위한 CI/CD 입문부터 고급 워크플로 설계까지

저자: OpenAI  
초판: 2026-03-18

---

# 머리말

소프트웨어 개발에서 반복 작업은 생각보다 많습니다.  
코드를 푸시할 때마다 테스트를 실행하고, 린트를 확인하고, 빌드 결과를 점검하고, 배포 준비를 하는 일은 모두 시간이 드는 작업입니다. 이러한 과정을 사람이 직접 수행하면 실수가 생기기 쉽고, 팀마다 방식이 달라져 품질 편차도 커집니다.

GitHub Actions는 이러한 반복 작업을 자동화하는 강력한 도구입니다. 저장소에서 일어나는 이벤트를 기준으로 테스트, 빌드, 패키징, 릴리스, 배포, 알림, 정기 작업 등을 코드로 정의하고 실행할 수 있습니다. 특히 GitHub를 중심으로 협업하는 팀이라면 별도의 CI 시스템을 따로 구축하지 않고도 자동화 체계를 빠르게 도입할 수 있다는 장점이 있습니다.

이 책은 GitHub Actions를 처음 접하는 독자도 차근차근 따라올 수 있도록 기초부터 시작합니다. 이후에는 실무에서 바로 사용할 수 있는 수준까지 도달할 수 있도록 테스트 자동화, 매트릭스 빌드, 보안, 재사용 워크플로, 배포 전략, 디버깅까지 폭넓게 다룹니다.

이 책의 목적은 단순히 YAML 문법을 설명하는 데 있지 않습니다.  
자동화를 설계하는 관점, 운영 환경에서 안전하게 배포하는 원칙, 재사용 가능한 워크플로를 만드는 습관까지 함께 익히는 것이 목표입니다.

---

# 이 책의 대상 독자

이 책은 다음과 같은 독자를 대상으로 합니다.

- GitHub는 사용하고 있지만 GitHub Actions는 처음인 개발자
- 테스트 자동화와 CI/CD를 시작하려는 팀
- 반복 작업을 코드로 관리하고 싶은 백엔드/프론트엔드 개발자
- 오픈소스 프로젝트 유지보수자
- 배포 파이프라인을 체계화하려는 DevOps 입문자

---

# 이 책을 읽는 방법

이 책은 크게 세 단계로 읽을 수 있습니다.

## 1. 입문 단계
1장부터 6장까지는 GitHub Actions의 핵심 개념과 기본 구조를 익히는 데 집중합니다.  
처음 접하는 독자는 반드시 이 부분을 먼저 읽고 예제를 직접 실행해보는 것을 권장합니다.

## 2. 실습 단계
7장부터 14장까지는 환경 변수, 출력값, 캐시, 테스트 자동화, 빌드, Docker, 보안, 매트릭스 전략 등을 다룹니다.  
이 단계에서는 직접 저장소를 만들어 워크플로를 반복 수정하며 익히는 것이 중요합니다.

## 3. 실무 적용 단계
15장부터 마지막 장까지는 재사용 가능한 워크플로, 승인 전략, 운영 배포, 디버깅, 실전 프로젝트 예제를 중심으로 구성됩니다.  
실제 서비스 저장소에 적용하기 전에 이 장들을 바탕으로 설계 원칙을 잡는 것을 추천합니다.

---

# 목차

1. GitHub Actions란 무엇인가
2. GitHub Actions 시작하기
3. 워크플로 YAML 기초
4. 이벤트와 트리거 이해하기
5. 잡과 스텝, 러너의 실행 구조
6. 액션 재사용하기
7. 환경 변수, 출력값, 컨텍스트
8. 아티팩트와 캐시
9. 테스트 자동화 실습
10. 빌드와 패키징 자동화
11. Docker와 GitHub Actions
12. 배포 자동화 기초
13. 시크릿과 보안
14. 매트릭스 빌드와 병렬 처리
15. 재사용 가능한 워크플로와 컴포지트 액션
16. 승인, 환경 보호, 운영 배포 전략
17. 문제 해결과 디버깅
18. 실전 프로젝트 1: Node.js 애플리케이션 CI/CD
19. 실전 프로젝트 2: Python 패키지 배포 자동화
20. 실전 프로젝트 3: 정적 사이트 자동 배포
21. 베스트 프랙티스
22. 용어집
23. 연습문제
24. 맺음말

---

# 1장. GitHub Actions란 무엇인가

GitHub Actions는 GitHub 저장소에서 발생하는 이벤트를 기반으로 자동화 작업을 실행하는 기능입니다.  
가장 대표적인 용도는 CI(Continuous Integration)와 CD(Continuous Delivery/Deployment)이지만, 실제로는 그보다 더 넓은 범위의 자동화를 처리할 수 있습니다.

예를 들어 다음과 같은 작업을 자동화할 수 있습니다.

- 코드 푸시 시 테스트 자동 실행
- Pull Request 생성 시 린트와 빌드 검증
- 태그 생성 시 릴리스 패키지 업로드
- 특정 시각마다 정기 스크립트 실행
- 이슈 생성 시 자동 라벨 부여
- 문서 변경 감지 후 정적 사이트 재배포

즉 GitHub Actions는 단순한 “테스트 실행 도구”가 아니라, 개발 프로세스 전체를 자동화할 수 있는 실행 플랫폼입니다.

## 1.1 왜 자동화가 필요한가

수동 작업은 느리고, 실수가 잦고, 일관성을 유지하기 어렵습니다.  
개발자가 직접 테스트를 실행하고, 빌드 결과를 확인하고, 배포 절차를 수행하는 방식은 프로젝트가 커질수록 한계가 드러납니다.

자동화의 장점은 다음과 같습니다.

- 사람이 놓칠 수 있는 검증 절차를 항상 실행할 수 있다.
- 코드 품질을 일정한 기준으로 유지할 수 있다.
- 협업 시 공통된 개발 규칙을 정착시킬 수 있다.
- 배포 시간을 줄이고 반복 가능성을 높일 수 있다.
- 실패 지점을 빠르게 발견할 수 있다.

## 1.2 GitHub Actions의 핵심 구성 요소

GitHub Actions를 이해하려면 다섯 가지 핵심 개념을 먼저 알아야 합니다.

### Workflow
자동화 전체를 정의한 단위입니다.  
YAML 파일 하나가 하나의 워크플로가 됩니다.

### Event
워크플로를 실행시키는 계기입니다.  
예를 들어 `push`, `pull_request`, `workflow_dispatch`, `schedule` 등이 있습니다.

### Job
워크플로 내부에서 실행되는 작업 단위입니다.  
하나의 워크플로에는 여러 개의 job이 있을 수 있습니다.

### Step
job 안에서 순서대로 실행되는 세부 단계입니다.  
보통 명령어 실행이나 액션 호출이 step으로 표현됩니다.

### Runner
job이 실제로 실행되는 환경입니다.  
Ubuntu, Windows, macOS 또는 self-hosted 환경을 사용할 수 있습니다.

## 1.3 CI/CD와 GitHub Actions

CI는 코드가 변경될 때마다 자동으로 테스트와 검증을 수행하는 개념입니다.  
CD는 검증된 결과물을 자동 또는 반자동으로 배포하는 과정을 뜻합니다.

GitHub Actions는 이 둘을 모두 구현할 수 있습니다.

- CI 예시: push → test → lint → build
- CD 예시: tag push → package build → artifact upload → deploy

## 1.4 학습 관점에서 중요한 점

GitHub Actions를 배울 때 가장 흔한 실수는 YAML 문법만 외우는 것입니다.  
하지만 실제로 중요한 것은 다음 세 가지입니다.

- 어떤 이벤트에서 무엇을 실행해야 하는가
- 어떤 작업을 하나의 job으로 분리해야 하는가
- 실패했을 때 어디서 원인을 추적할 것인가

이 책은 따라서 단순 문법 설명보다 “설계와 운영” 관점까지 함께 다룹니다.

## 장 요약

- GitHub Actions는 GitHub 이벤트 기반 자동화 플랫폼이다.
- CI/CD뿐 아니라 다양한 저장소 작업을 자동화할 수 있다.
- workflow, event, job, step, runner 개념이 핵심이다.
- YAML 문법보다 자동화 흐름 설계가 더 중요하다.

---

# 2장. GitHub Actions 시작하기

GitHub Actions 워크플로는 저장소 내부의 `.github/workflows/` 디렉터리에 YAML 파일로 저장합니다.

가장 간단한 예제는 다음과 같습니다.

```yaml name=.github/workflows/ci.yml
name: Basic CI

on: [push]

jobs:
  hello:
    runs-on: ubuntu-latest
    steps:
      - name: 코드 체크아웃
        uses: actions/checkout@v4

      - name: 인사 출력
        run: echo "Hello, GitHub Actions!"
```

## 2.1 워크플로 파일 위치

워크플로 파일은 반드시 다음 경로에 있어야 합니다.

`.github/workflows/파일명.yml`

예를 들어 다음과 같은 구조를 가집니다.

- `.github/workflows/ci.yml`
- `.github/workflows/test.yml`
- `.github/workflows/deploy.yml`

## 2.2 기본 구조 읽기

예제의 각 요소를 살펴보겠습니다.

- `name`: 워크플로 이름
- `on`: 실행 조건
- `jobs`: 실행할 작업 목록
- `runs-on`: 실행 환경
- `steps`: 작업 내부 단계들
- `uses`: 액션 사용
- `run`: 쉘 명령 실행

## 2.3 첫 실행 과정

이 워크플로가 실행되는 흐름은 다음과 같습니다.

1. 개발자가 저장소에 코드를 push한다.
2. GitHub가 `push` 이벤트를 감지한다.
3. 해당 이벤트와 연결된 워크플로를 찾는다.
4. 러너를 준비한다.
5. job을 시작한다.
6. step을 순서대로 실행한다.
7. 실행 결과를 UI에 기록한다.

## 2.4 최소 예제로 감 잡기

더 단순한 예제도 가능합니다.

```yaml name=.github/workflows/minimal.yml
name: Minimal Example

on:
  workflow_dispatch:

jobs:
  sample:
    runs-on: ubuntu-latest
    steps:
      - run: echo "수동 실행 예제"
```

이 예제는 저장소 화면에서 직접 수동 실행할 수 있습니다.

## 2.5 처음 실습할 때 추천 순서

처음에는 다음 순서로 익히는 것이 좋습니다.

1. `workflow_dispatch`로 수동 실행
2. `push` 이벤트 추가
3. 체크아웃 액션 사용
4. 간단한 테스트 명령 추가
5. 실패 로그 확인

## 장 요약

- 워크플로는 `.github/workflows/` 아래의 YAML 파일이다.
- `name`, `on`, `jobs`, `steps`가 기본 구조다.
- `workflow_dispatch`를 사용하면 처음 실습하기 좋다.
- 가장 먼저 “실행 흐름”을 눈으로 익히는 것이 중요하다.

---

# 3장. 워크플로 YAML 기초

GitHub Actions는 YAML 형식으로 정의됩니다.  
따라서 YAML 문법을 이해해야 워크플로를 정확하게 작성할 수 있습니다.

## 3.1 YAML의 기본 규칙

YAML은 공백 기반 구조를 사용합니다.  
다음 규칙은 반드시 기억해야 합니다.

- 들여쓰기는 공백으로 한다.
- 탭은 사용하지 않는다.
- 계층 구조는 들여쓰기로 표현한다.
- 리스트는 `-` 기호를 사용한다.
- key-value 형식으로 값을 표현한다.

예시를 보겠습니다.

```yaml name=example.yml
name: Example

on:
  push:
    branches:
      - main
      - develop
```

## 3.2 자주 사용하는 키

GitHub Actions에서 자주 쓰는 최상위 키는 다음과 같습니다.

- `name`
- `on`
- `permissions`
- `env`
- `defaults`
- `concurrency`
- `jobs`

job 내부에서는 다음 키를 자주 사용합니다.

- `runs-on`
- `needs`
- `if`
- `strategy`
- `steps`
- `outputs`

step 내부에서는 다음 키를 자주 사용합니다.

- `name`
- `uses`
- `run`
- `with`
- `env`
- `id`
- `if`

## 3.3 배열과 맵 구조 익히기

다음은 `steps`가 배열이라는 점을 보여주는 예제입니다.

```yaml name=steps-example.yml
jobs:
  demo:
    runs-on: ubuntu-latest
    steps:
      - name: 첫 번째 단계
        run: echo "one"

      - name: 두 번째 단계
        run: echo "two"
```

각 `-`가 하나의 step입니다.

## 3.4 문자열과 표현식

GitHub Actions는 `${{ ... }}` 문법을 사용해 표현식을 평가합니다.

```yaml name=expression.yml
jobs:
  demo:
    runs-on: ubuntu-latest
    steps:
      - run: echo "브랜치 이름은 ${{ github.ref_name }}"
```

YAML 문자열과 표현식을 혼동하면 오류가 발생할 수 있습니다.  
특히 조건문과 env 설정에서 주의가 필요합니다.

## 3.5 초보자가 자주 하는 실수

- 탭 사용
- 잘못된 들여쓰기
- `steps` 아래에 `-` 누락
- `uses`와 `run` 혼동
- 표현식 괄호 누락
- 브랜치 필터 오타

## 장 요약

- YAML은 공백 기반 문법이므로 들여쓰기가 매우 중요하다.
- GitHub Actions는 YAML 위에 자체 표현식 문법을 추가해 사용한다.
- 기본 구조를 이해하면 대부분의 워크플로를 읽을 수 있다.
- 작은 문법 실수가 전체 실행 실패로 이어질 수 있다.

---

# 4장. 이벤트와 트리거 이해하기

워크플로는 이벤트가 발생할 때 실행됩니다.  
이 이벤트를 정확히 이해해야 원하는 시점에 자동화를 동작시킬 수 있습니다.

## 4.1 대표 이벤트

GitHub Actions에서 자주 사용하는 이벤트는 다음과 같습니다.

- `push`
- `pull_request`
- `workflow_dispatch`
- `schedule`
- `release`
- `issues`
- `issue_comment`

## 4.2 push 이벤트

가장 기본적인 이벤트입니다.

```yaml name=.github/workflows/on-push.yml
name: On Push

on:
  push:

jobs:
  demo:
    runs-on: ubuntu-latest
    steps:
      - run: echo "push 이벤트 발생"
```

특정 브랜치로 제한할 수도 있습니다.

```yaml name=.github/workflows/on-push-main.yml
name: On Main Push

on:
  push:
    branches:
      - main

jobs:
  demo:
    runs-on: ubuntu-latest
    steps:
      - run: echo "main 브랜치 push"
```

## 4.3 pull_request 이벤트

코드 리뷰 단계에서 검증을 수행하기 좋습니다.

```yaml name=.github/workflows/pr.yml
name: Pull Request Check

on:
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - run: echo "PR 검증"
```

## 4.4 workflow_dispatch 이벤트

수동으로 실행할 수 있는 이벤트입니다.

```yaml name=.github/workflows/manual.yml
name: Manual Workflow

on:
  workflow_dispatch:

jobs:
  manual-job:
    runs-on: ubuntu-latest
    steps:
      - run: echo "수동 실행"
```

운영 배포나 관리용 스크립트에 자주 사용됩니다.

## 4.5 schedule 이벤트

정기 작업에 적합합니다.

```yaml name=.github/workflows/schedule.yml
name: Nightly Schedule

on:
  schedule:
    - cron: '0 0 * * *'

jobs:
  nightly:
    runs-on: ubuntu-latest
    steps:
      - run: echo "매일 자정 실행"
```

## 4.6 paths와 branches 필터

이벤트는 세부 조건으로 필터링할 수 있습니다.

```yaml name=.github/workflows/path-filter.yml
name: Path Filter

on:
  push:
    branches:
      - main
    paths:
      - 'src/**'
      - '.github/workflows/**'

jobs:
  filtered:
    runs-on: ubuntu-latest
    steps:
      - run: echo "특정 경로가 변경되었을 때만 실행"
```

## 장 요약

- 워크플로는 이벤트 기반으로 실행된다.
- `push`, `pull_request`, `workflow_dispatch`, `schedule`이 가장 자주 쓰인다.
- 브랜치와 경로 필터를 사용하면 불필요한 실행을 줄일 수 있다.
- 자동화는 “언제 실행할 것인가”부터 설계해야 한다.

---

# 5장. 잡과 스텝, 러너의 실행 구조

GitHub Actions에서 실제 실행 단위를 이해하려면 job, step, runner의 관계를 알아야 합니다.

## 5.1 Job이란 무엇인가

job은 워크플로 안의 큰 작업 단위입니다.  
하나의 workflow에는 여러 job이 있을 수 있으며, 기본적으로 병렬 실행됩니다.

```yaml name=.github/workflows/multi-job.yml
name: Multi Job

on: [push]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - run: echo "빌드"

  test:
    runs-on: ubuntu-latest
    steps:
      - run: echo "테스트"
```

## 5.2 Step이란 무엇인가

step은 job 안에서 순차적으로 실행되는 단계입니다.

```yaml name=steps.yml
jobs:
  sample:
    runs-on: ubuntu-latest
    steps:
      - run: echo "1단계"
      - run: echo "2단계"
      - run: echo "3단계"
```

step은 이전 step이 성공해야 다음 step으로 진행되는 것이 일반적입니다.

## 5.3 needs로 의존성 만들기

job 간 순서를 제어하려면 `needs`를 사용합니다.

```yaml name=.github/workflows/needs.yml
name: Job Dependencies

on: [push]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - run: echo "build"

  test:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - run: echo "test after build"
```

## 5.4 Runner란 무엇인가

runner는 job이 실제 실행되는 머신 또는 환경입니다.  
대표적으로 다음과 같은 GitHub-hosted runner가 있습니다.

- `ubuntu-latest`
- `windows-latest`
- `macos-latest`

또한 조직이 직접 운영하는 self-hosted runner도 사용할 수 있습니다.

## 5.5 실행 구조를 이해하는 이유

실행 구조를 이해하면 다음과 같은 설계가 쉬워집니다.

- 테스트와 빌드를 병렬로 나누기
- 배포 job을 최종 단계로 연결하기
- OS별 검증을 분리하기
- 실패 시 어느 단계가 문제인지 빠르게 찾기

## 장 요약

- job은 큰 실행 단위, step은 세부 실행 단계다.
- job은 기본적으로 병렬, step은 기본적으로 순차 실행된다.
- `needs`를 사용하면 job 간 의존성을 만들 수 있다.
- runner는 실제 실행 환경이다.

---

# 6장. 액션 재사용하기

GitHub Actions의 강력한 장점 중 하나는 이미 만들어진 액션을 재사용할 수 있다는 점입니다.

## 6.1 액션이란 무엇인가

액션은 반복적으로 사용하는 자동화 로직을 묶어둔 재사용 단위입니다.  
예를 들어 소스코드 체크아웃, 특정 언어 런타임 설치, 캐시 설정, 아티팩트 업로드 등을 액션으로 손쉽게 사용할 수 있습니다.

## 6.2 가장 많이 쓰는 액션

- `actions/checkout`
- `actions/setup-node`
- `actions/setup-python`
- `actions/cache`
- `actions/upload-artifact`
- `actions/download-artifact`

## 6.3 uses와 run의 차이

- `uses`: 이미 만들어진 액션을 호출
- `run`: 셸 명령을 직접 실행

예제:

```yaml name=.github/workflows/node-ci.yml
name: Node CI

on: [push]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: 20

      - run: npm ci
      - run: npm test
```

## 6.4 with 입력값

액션은 `with`를 사용해 입력값을 받을 수 있습니다.

```yaml name=with-example.yml
steps:
  - uses: actions/setup-node@v4
    with:
      node-version: 20
```

## 6.5 액션 사용 시 주의점

- 액션 버전을 명시한다.
- 외부 액션의 신뢰성을 검토한다.
- 입력값이 정확한지 확인한다.
- 보안이 중요한 경우 권한 범위를 점검한다.

## 장 요약

- 액션은 재사용 가능한 자동화 구성 요소다.
- `uses`로 외부 액션을 호출하고, `run`으로 직접 명령을 실행한다.
- 체크아웃, 런타임 설정, 캐시, 아티팩트 업로드는 대표적인 액션 활용 사례다.
- 버전 관리와 보안 점검이 중요하다.

---

# 7장. 환경 변수, 출력값, 컨텍스트

실전 워크플로에서는 데이터 전달이 중요합니다.  
GitHub Actions는 환경 변수, step 출력값, 컨텍스트를 통해 실행 중 데이터를 다룰 수 있습니다.

## 7.1 환경 변수 사용하기

```yaml name=.github/workflows/env.yml
name: Env Example

on: [push]

env:
  APP_NAME: demo-app

jobs:
  print-env:
    runs-on: ubuntu-latest
    steps:
      - run: echo "App is $APP_NAME"
```

환경 변수는 workflow, job, step 범위에서 각각 정의할 수 있습니다.

## 7.2 출력값 만들기

step에서 값을 생성하고 다음 job으로 전달할 수 있습니다.

```yaml name=.github/workflows/output.yml
name: Output Example

on: [push]

jobs:
  first:
    runs-on: ubuntu-latest
    outputs:
      version: ${{ steps.setver.outputs.version }}
    steps:
      - id: setver
        run: echo "version=1.0.0" >> $GITHUB_OUTPUT

  second:
    needs: first
    runs-on: ubuntu-latest
    steps:
      - run: echo "Version is ${{ needs.first.outputs.version }}"
```

## 7.3 컨텍스트 이해하기

컨텍스트는 GitHub Actions가 제공하는 실행 정보 객체입니다.

자주 사용하는 컨텍스트는 다음과 같습니다.

- `github`
- `env`
- `vars`
- `secrets`
- `steps`
- `runner`
- `matrix`
- `needs`

예를 들어 브랜치 이름을 출력할 수 있습니다.

```yaml name=context.yml
steps:
  - run: echo "${{ github.ref_name }}"
```

## 7.4 언제 무엇을 써야 하는가

- 고정 설정값: `env`
- 비밀 값: `secrets`
- 이전 step 결과: `steps.<id>.outputs`
- 이전 job 결과: `needs.<job>.outputs`
- GitHub 이벤트 정보: `github`

## 장 요약

- 환경 변수는 공통 설정값 관리에 유용하다.
- 출력값은 step과 job 사이의 데이터 전달에 사용된다.
- 컨텍스트는 실행 환경과 이벤트 메타데이터를 제공한다.
- 값의 범위를 구분해서 사용하는 습관이 중요하다.

---

# 8장. 아티팩트와 캐시

워크플로를 효율적으로 만들려면 실행 결과물과 의존성 데이터를 잘 다뤄야 합니다.  
그때 사용하는 대표 기능이 아티팩트와 캐시입니다.

## 8.1 아티팩트란 무엇인가

아티팩트는 워크플로 실행 도중 생성된 파일을 저장하고 나중에 다운로드하거나 다른 단계에서 활용할 수 있게 해주는 기능입니다.

```yaml name=.github/workflows/artifact.yml
name: Artifact Example

on: [push]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - run: mkdir dist && echo "hello" > dist/result.txt

      - uses: actions/upload-artifact@v4
        with:
          name: build-output
          path: dist/
```

## 8.2 캐시란 무엇인가

캐시는 반복 설치 비용이 큰 파일을 재사용하기 위한 기능입니다.  
주로 패키지 매니저 캐시에 사용됩니다.

```yaml name=.github/workflows/cache.yml
name: Cache Example

on: [push]

jobs:
  cache-demo:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: npm

      - run: npm ci
      - run: npm test
```

## 8.3 아티팩트와 캐시의 차이

- 아티팩트: 실행 결과물을 저장
- 캐시: 이후 실행 속도 개선을 위해 재사용 데이터 저장

## 8.4 실무 팁

- 테스트 리포트는 아티팩트로 보관한다.
- 빌드 결과물도 아티팩트로 관리할 수 있다.
- 의존성 캐시는 키 충돌과 무효화 전략을 함께 고려해야 한다.

## 장 요약

- 아티팩트는 결과물 저장, 캐시는 성능 최적화 목적이다.
- 둘을 혼동하지 말고 목적에 맞게 사용해야 한다.
- 속도와 추적성을 동시에 개선할 수 있다.

---

# 9장. 테스트 자동화 실습

테스트 자동화는 GitHub Actions를 도입할 때 가장 먼저 시도할 만한 작업입니다.

## 9.1 Node.js 테스트 예제

```yaml name=.github/workflows/test-node.yml
name: Test Node App

on:
  pull_request:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: npm

      - run: npm ci
      - run: npm run lint
      - run: npm test
```

## 9.2 Python 테스트 예제

```yaml name=.github/workflows/test-python.yml
name: Test Python App

on:
  pull_request:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - run: pip install -r requirements.txt
      - run: pytest
```

## 9.3 테스트 자동화 설계 팁

- PR 생성 시 반드시 실행되도록 한다.
- main 브랜치 push에도 실행한다.
- 린트와 테스트를 분리할지 함께 둘지 결정한다.
- 실패 로그를 읽기 쉽게 만든다.

## 장 요약

- 테스트 자동화는 Actions 학습의 가장 좋은 출발점이다.
- 언어별 런타임 설정 액션을 적극 활용한다.
- PR 검증 루틴으로 연결하면 협업 품질이 올라간다.

---

# 10장. 빌드와 패키징 자동화

코드 검증이 끝났다면, 다음 단계는 결과물 생성입니다.

## 10.1 태그 기반 빌드

```yaml name=.github/workflows/build.yml
name: Build Project

on:
  push:
    tags:
      - 'v*.*.*'

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: echo "빌드 수행"
      - run: mkdir out && echo "binary" > out/app.bin

      - uses: actions/upload-artifact@v4
        with:
          name: package
          path: out/
```

## 10.2 왜 태그 기반이 유용한가

버전 릴리스 시점에만 빌드를 수행할 수 있어, 릴리스 기준이 명확해집니다.

## 10.3 빌드 자동화 체크리스트

- 빌드 조건이 명확한가
- 빌드 산출물이 보관되는가
- 실패 시 원인을 추적할 수 있는가
- 릴리스 정책과 연결되어 있는가

## 장 요약

- 빌드는 테스트 이후의 핵심 단계다.
- 태그 이벤트를 활용하면 릴리스 자동화와 자연스럽게 연결된다.
- 결과물 보관 전략이 중요하다.

---

# 11장. Docker와 GitHub Actions

컨테이너 중심 개발에서는 Docker 자동화가 매우 중요합니다.

## 11.1 기본 Docker 빌드

```yaml name=.github/workflows/docker.yml
name: Docker Build

on:
  push:
    branches: [main]

jobs:
  docker:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: docker build -t my-app:latest .
```

## 11.2 확장 가능한 방향

실무에서는 다음과 같은 요구가 추가됩니다.

- 컨테이너 레지스트리 로그인
- 태그 전략 관리
- 브랜치별 이미지 이름 분리
- 멀티 아키텍처 빌드
- 보안 스캔

## 11.3 Docker 자동화 설계 팁

- `latest`만 사용하지 말고 버전 태그를 병행한다.
- 배포 환경별 이미지 전략을 분리한다.
- 이미지 빌드와 푸시를 명확히 구분한다.

## 장 요약

- Docker 빌드는 Actions에서 자연스럽게 자동화할 수 있다.
- 실무에서는 인증, 태깅, 배포 전략까지 함께 고려해야 한다.
- 빌드와 배포를 분리하면 운영 안정성이 높아진다.

---

# 12장. 배포 자동화 기초

배포는 가장 강력하면서도 가장 신중해야 하는 자동화입니다.

## 12.1 기본 배포 흐름

보통 배포는 다음 순서로 진행됩니다.

1. 코드 체크아웃
2. 런타임 설치
3. 의존성 설치
4. 테스트
5. 빌드
6. 인증
7. 배포 실행

## 12.2 수동 배포 워크플로 예제

```yaml name=.github/workflows/deploy.yml
name: Deploy App

on:
  workflow_dispatch:

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - run: echo "배포 시작"
      - run: echo "서버 또는 클라우드로 배포"
```

## 12.3 왜 수동 배포부터 시작해야 하는가

초기에는 자동 배포보다 수동 배포가 안전합니다.  
파이프라인 검증이 충분히 끝난 후에만 완전 자동 배포로 확장하는 것이 좋습니다.

## 12.4 배포 자동화 설계 원칙

- 테스트 통과 이후에만 배포
- 운영 배포는 승인 단계 추가
- 비밀 값은 secrets로 관리
- 실패 시 롤백 전략 고려

## 장 요약

- 배포 자동화는 검증된 결과물을 안전하게 전달하는 과정이다.
- 처음에는 `workflow_dispatch` 기반 수동 실행이 적합하다.
- 운영 배포는 항상 통제와 검증을 포함해야 한다.

---

# 13장. 시크릿과 보안

자동화가 강력해질수록 보안의 중요성도 함께 커집니다.

## 13.1 왜 시크릿 관리가 중요한가

배포 토큰, API 키, 클라우드 자격 증명처럼 민감한 값이 노출되면 자동화 환경 자체가 공격 벡터가 될 수 있습니다.

## 13.2 기본 예제

```yaml name=.github/workflows/secret.yml
name: Secret Example

on: [push]

jobs:
  use-secret:
    runs-on: ubuntu-latest
    steps:
      - run: echo "토큰 사용"
        env:
          API_TOKEN: ${{ secrets.API_TOKEN }}
```

## 13.3 보안 원칙

- 시크릿을 코드에 직접 쓰지 않는다.
- 최소 권한 원칙을 적용한다.
- 외부 액션은 신뢰성과 버전을 검토한다.
- PR from fork 상황에서 시크릿 노출을 주의한다.
- `permissions`를 최소화한다.

## 13.4 권한 최소화 예제

```yaml name=permissions.yml
permissions:
  contents: read
```

필요한 권한만 명시하는 습관이 중요합니다.

## 장 요약

- 시크릿은 반드시 안전한 저장소에 보관해야 한다.
- Actions 보안은 권한, 외부 액션, 이벤트 특성을 함께 고려해야 한다.
- 편의성보다 안전성을 우선하는 설계가 필요하다.

---

# 14장. 매트릭스 빌드와 병렬 처리

여러 환경을 동시에 검증하려면 매트릭스 전략이 유용합니다.

## 14.1 Node.js 버전별 테스트

```yaml name=.github/workflows/matrix.yml
name: Matrix Build

on: [push]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        node-version: [18, 20, 22]
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node-version }}

      - run: npm ci
      - run: npm test
```

## 14.2 매트릭스가 필요한 이유

- 여러 런타임 버전 지원 검증
- 여러 운영체제 검증
- 구성 조합 자동 테스트

## 14.3 주의할 점

매트릭스는 강력하지만 실행 시간이 늘어나고 비용도 증가할 수 있습니다.  
따라서 꼭 필요한 조합만 선택해야 합니다.

## 장 요약

- 매트릭스 전략으로 다양한 환경을 자동 검증할 수 있다.
- 병렬 처리로 품질 검증 범위를 넓힐 수 있다.
- 조합 수가 너무 많아지지 않도록 주의해야 한다.

---

# 15장. 재사용 가능한 워크플로와 컴포지트 액션

프로젝트가 커질수록 공통 로직을 재사용하는 구조가 중요해집니다.

## 15.1 재사용 가능한 워크플로

```yaml name=.github/workflows/reusable.yml
name: Reusable Workflow

on:
  workflow_call:

jobs:
  reusable-job:
    runs-on: ubuntu-latest
    steps:
      - run: echo "재사용 가능한 워크플로"
```

호출 예제:

```yaml name=.github/workflows/caller.yml
name: Caller

on: [push]

jobs:
  call-reusable:
    uses: ./.github/workflows/reusable.yml
```

## 15.2 컴포지트 액션

```yaml name=.github/actions/setup-app/action.yml
name: Setup App
description: Setup dependencies
runs:
  using: composite
  steps:
    - run: echo "설정 중"
      shell: bash
```

## 15.3 언제 무엇을 써야 하는가

- 여러 저장소에서 공통 CI 로직 재사용: 재사용 워크플로
- 여러 step 묶음을 액션처럼 재사용: 컴포지트 액션

## 장 요약

- 자동화가 커질수록 중복 제거가 중요하다.
- 재사용 워크플로와 컴포지트 액션은 유지보수성을 크게 높인다.
- 공통 로직은 초기에 구조화해두는 편이 유리하다.

---

# 16장. 승인, 환경 보호, 운영 배포 전략

운영 환경 배포는 개발 환경 배포와 다르게 통제가 핵심입니다.

## 16.1 환경 분리

일반적으로 다음과 같이 나눕니다.

- dev
- staging
- production

## 16.2 운영 배포에 필요한 요소

- 환경 보호
- 승인자 지정
- 대기 시간
- 브랜치 보호 정책
- 수동 검토 단계

## 16.3 권장 배포 흐름

1. 개발 브랜치에서 테스트
2. main 병합 후 staging 배포
3. 승인 후 production 배포

## 장 요약

- 운영 배포는 자동화만큼 통제가 중요하다.
- 환경 분리와 승인 절차를 통해 사고를 줄일 수 있다.
- 배포 전략은 팀 운영 모델과 함께 설계해야 한다.

---

# 17장. 문제 해결과 디버깅

워크플로가 실패하는 것은 자연스러운 일입니다.  
중요한 것은 빠르게 원인을 찾고 재발을 줄이는 것입니다.

## 17.1 실패 시 확인 순서

1. 로그를 읽는다.
2. 어느 step에서 실패했는지 확인한다.
3. 입력값과 환경 변수를 점검한다.
4. 액션 버전을 확인한다.
5. 권한 문제를 검토한다.
6. 로컬에서 재현해본다.

## 17.2 디버깅 팁

- 중간값을 `echo`로 출력한다.
- 실패 시 아티팩트를 업로드한다.
- 큰 job을 작은 job으로 분리한다.
- 조건문과 표현식을 하나씩 확인한다.

## 장 요약

- 로그 읽기 능력이 디버깅의 핵심이다.
- 실패 지점을 좁히는 구조화가 중요하다.
- 관찰 가능한 워크플로를 만드는 습관이 필요하다.

---

# 18장. 실전 프로젝트 1: Node.js 애플리케이션 CI/CD

```yaml name=.github/workflows/node-cicd.yml
name: Node CI/CD

on:
  push:
    branches: [main]
  pull_request:

permissions:
  contents: read

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: npm
      - run: npm ci
      - run: npm run lint
      - run: npm test

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci
      - run: npm run build

  deploy:
    if: github.ref == 'refs/heads/main'
    needs: build
    runs-on: ubuntu-latest
    steps:
      - run: echo "배포 실행"
```

## 해설

이 워크플로는 다음과 같은 흐름을 가집니다.

- PR 또는 main push에서 시작
- 먼저 테스트 실행
- 테스트 통과 후 빌드
- main 브랜치일 때만 배포

이 구조는 가장 기본적인 CI/CD 패턴으로 활용할 수 있습니다.

---

# 19장. 실전 프로젝트 2: Python 패키지 배포 자동화

```yaml name=.github/workflows/python-package.yml
name: Python Package

on:
  push:
    tags:
      - 'v*.*.*'

jobs:
  build-and-publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install build
      - run: python -m build
      - run: echo "패키지 업로드"
```

## 해설

태그 기반 릴리스에 맞춰 패키지를 빌드하는 전형적인 구조입니다.  
여기에 패키지 저장소 인증과 업로드 step을 추가하면 배포 파이프라인이 완성됩니다.

---

# 20장. 실전 프로젝트 3: 정적 사이트 자동 배포

```yaml name=.github/workflows/pages.yml
name: Deploy Static Site

on:
  push:
    branches: [main]

jobs:
  deploy-pages:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: echo "정적 사이트 빌드"
      - run: echo "정적 사이트 배포"
```

## 해설

문서 사이트, 블로그, 제품 소개 페이지처럼 정적 사이트는 자동 배포 구조를 가장 먼저 적용하기 좋은 대상입니다.

---

# 21장. 베스트 프랙티스

## 21.1 설계 원칙

- 워크플로는 작게 시작한다.
- 실패를 빨리 드러내는 구조를 만든다.
- 공통 로직은 재사용한다.
- 권한은 최소화한다.
- 시크릿은 코드에 쓰지 않는다.
- 운영 배포에는 통제를 둔다.

## 21.2 유지보수 원칙

- 워크플로 이름을 명확히 작성한다.
- step 이름도 읽기 쉽게 쓴다.
- 주석보다 구조를 명확히 만든다.
- 외부 액션 버전 정책을 정한다.
- 오래된 자동화는 주기적으로 정리한다.

## 21.3 팀 적용 팁

- 모든 저장소에 동일한 템플릿을 강요하지 않는다.
- 공통 정책과 저장소별 예외를 분리한다.
- 배포 자동화는 작은 범위부터 확대한다.

## 장 요약

- 좋은 워크플로는 단순하고 관찰 가능하며 안전하다.
- 자동화의 목적은 복잡성 증가가 아니라 반복 작업 감소다.
- 유지보수 가능한 구조가 장기적으로 가장 중요하다.

---

# 22장. 용어집

## Workflow
자동화 전체를 정의한 YAML 파일 단위

## Event
워크플로 실행을 유발하는 GitHub 이벤트

## Job
워크플로 내부의 실행 작업 단위

## Step
job 내부의 순차 실행 단계

## Runner
job이 실제로 실행되는 환경

## Action
재사용 가능한 자동화 구성 요소

## Artifact
워크플로 실행 결과물 파일

## Cache
실행 속도 개선을 위한 재사용 저장 데이터

## Secret
민감 정보를 안전하게 저장하는 값

## Matrix
여러 환경 조합을 반복 실행하는 전략

---

# 23장. 연습문제

1. `workflow_dispatch`로 수동 실행되는 워크플로를 작성하라.
2. `push` 이벤트에서 main 브랜치에만 실행되도록 제한하라.
3. Node.js 18, 20, 22 버전 매트릭스 테스트를 구성하라.
4. 테스트 결과 파일을 아티팩트로 업로드하라.
5. `needs`를 사용해 build job이 test job 이후 실행되게 하라.
6. `secrets.DEPLOY_TOKEN`을 사용하는 배포 step을 작성하라.
7. 재사용 가능한 워크플로를 만들고 다른 워크플로에서 호출하라.
8. 운영 배포에 승인 단계를 두는 전략을 설명하라.

## 예시 해설 방향

연습문제는 단순 정답 암기가 아니라 다음을 설명할 수 있어야 합니다.

- 왜 해당 이벤트를 선택했는가
- 왜 job을 분리했는가
- 왜 시크릿/권한/아티팩트 구성이 필요한가

---

# 24장. 맺음말

GitHub Actions는 단순한 CI 도구가 아니라 개발 과정을 코드로 정의하고 개선하는 자동화 플랫폼입니다.  
처음에는 한 개의 워크플로와 두세 개의 step으로 시작할 수 있습니다. 하지만 그 작은 자동화가 쌓이면 팀의 품질 체계와 배포 문화 자체를 바꾸게 됩니다.

중요한 것은 복잡한 자동화를 빠르게 만드는 것이 아닙니다.  
작고 명확하며 안전한 자동화를 만들고, 그것을 점진적으로 개선하는 것입니다.

이 책이 GitHub Actions를 처음 배우는 독자에게는 탄탄한 입문서가,  
이미 사용 중인 실무자에게는 구조를 재점검하는 참고서가 되기를 바랍니다.

---

# 부록 A. 자주 쓰는 짧은 예제 모음

## PR에서만 실행

```yaml
on:
  pull_request:
```

## 특정 브랜치 제외

```yaml
on:
  push:
    branches-ignore:
      - experimental
```

## 특정 경로 변경 시만 실행

```yaml
on:
  push:
    paths:
      - 'src/**'
      - '.github/workflows/**'
```

## 조건부 실행

```yaml
steps:
  - name: main 브랜치일 때만
    if: github.ref == 'refs/heads/main'
    run: echo "main only"
```

## 수동 실행 입력값 받기

```yaml
on:
  workflow_dispatch:
    inputs:
      environment:
        description: 배포 환경
        required: true
        default: staging
```

---

# 부록 B. 추천 학습 순서

- 1회독: 1장~6장
- 2회독: 7장~14장
- 3회독: 15장~21장
- 실습: 18장~20장 예제를 직접 저장소에서 실행
- 복습: 연습문제 풀이와 자신만의 워크플로 설계

---
---
## 🔗 관련 문서
- [[gh-cli-guide]]
- [[비개발자를 위한 AI 코딩 및 버전 관리 시스템(Git)]]
- [[Bedrock]]
- [[PE 와 IDP 정리]]
