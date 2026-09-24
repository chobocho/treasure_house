# 주장 대장 — 이 덱이 적는 모든 사실의 출처

> **규칙: 슬라이드에 적기 전에 여기 먼저 적는다.** (PLAN.md §0.4)
>
> 날짜·버전 번호·사람 이름·인용문·제안 번호·발표 제목·성능 수치 — 기억으로
> 적을 수 있을 것 같은 것일수록 반드시 틀린다. 한 줄을 여기 적는 일은 30초지만,
> 틀린 한 줄을 독자가 믿는 일은 되돌릴 수 없다.
>
> 출처의 우선순위 (위가 강하다):
>
> 1. `docs/` 에 받아 둔 공식 문서 — 릴리스 노트(go.dev/doc/go1.N), 릴리스
>    페이지(go.dev/doc/devel/release), API 목록(api/go1.N.txt), 명세, go1compat.
> 2. golang/go 저장소 — GitHub API·googlesource 의 태그 날짜와 커밋 메시지.
> 3. go.dev/blog · 제안 저장소(golang/proposal) · FAQ.
> 4. 위키백과 — **그 문서의 각주를 따라가 원출처를 확인한 경우에만.**
>
> 근거를 못 찾은 문장은 둘 중 하나다: 빼거나,
> 슬라이드에 `<span class="unv">미확인</span>` 을 붙여 모른다고 적는다.
> 성능 수치("GC 멈춤 10 ms 아래")는 노트·블로그를 **그대로 인용**하고 CITE 를
> 단다 — 이 기계에서 재지도, 달리 반올림하지도 않는다.
>
> **지식 기준일 규율** — Go 1.26·1.27 과 1.28 초안은 모델 지식의 끝이거나
> 그 밖이다. 그 부분은 만들 때 받은 `docs/` 로만 쓰고 "2026-09 기준" 을
> 박는다. 1.28 은 초안이라 바뀔 수 있다고 표지에 적는다. (PLAN.md §0.5)
>
> **버전 표기 규칙** — 산문의 `1.N` 은 이 파일이나 `data/*.tsv` 에 `go1.N`
> 꼴로 있어야 한다(`make claims-check`). 릴리스 날짜는 3단계부터
> `data/releases.tsv` 가 맡고, 슬라이드에는 `<!--REL v=1.N-->` 로만 싣는다.

## 적는 꼴

한 줄에 주장 하나. 칸은 넷이다.

| 주장 | 출처 | 확인한 방법 | 확인한 날 |
|---|---|---|---|
| go1 은 2012-03-28 에 나왔다 | https://go.dev/doc/devel/release | curl 로 받은 페이지의 "go1 (released 2012-03-28)" | 2026-09-24 |
| go1.1 은 2013-05-13 에 나왔다 | https://go.dev/doc/devel/release | 같은 페이지의 "go1.1 (released 2013-05-13)" | 2026-09-24 |
| go1.4 는 2014-12-10 에 나왔다 | https://go.dev/doc/devel/release | 같은 페이지의 "go1.4 (released 2014-12-10)" | 2026-09-24 |
| go1.5 는 2015-08-19 에 나왔다 | https://go.dev/doc/devel/release | 같은 페이지의 "go1.5 (released 2015-08-19)" | 2026-09-24 |
| go1.10 은 2018-02-16 에 나왔다 | https://go.dev/doc/devel/release | 같은 페이지의 "go1.10 (released 2018-02-16)" | 2026-09-24 |
| go1.11 은 2018-08-24 에 나왔다 | https://go.dev/doc/devel/release | 같은 페이지의 "go1.11 (released 2018-08-24)" | 2026-09-24 |
| go1.17 은 2021-08-16 에 나왔다 | https://go.dev/doc/devel/release | 같은 페이지의 "go1.17 (released 2021-08-16)" | 2026-09-24 |
| go1.18 은 2022-03-15 에 나왔다 | https://go.dev/doc/devel/release | 같은 페이지의 "go1.18 (released 2022-03-15)" | 2026-09-24 |
| go1.20 은 2023-02-01 에 나왔다 | https://go.dev/doc/devel/release | 같은 페이지의 "go1.20 (released 2023-02-01)" | 2026-09-24 |
| go1.21 은 2023-08-08 에 나왔다(표기는 go1.21.0) | https://go.dev/doc/devel/release | 같은 페이지의 "go1.21.0 (released 2023-08-08)" | 2026-09-24 |
| go1.24 는 2025-02-11 에 나왔다(표기는 go1.24.0) | https://go.dev/doc/devel/release | 같은 페이지의 "go1.24.0 (released 2025-02-11)" | 2026-09-24 |
| go1.25 는 2025-08-12 에 나왔다(표기는 go1.25.0) | https://go.dev/doc/devel/release | 같은 페이지의 "go1.25.0 (released 2025-08-12)" | 2026-09-24 |
| go1.27 은 2026-08-19 에 나왔다(표기는 go1.27.0) | https://go.dev/doc/devel/release | 같은 페이지의 "go1.27.0 (released 2026-08-19)" | 2026-09-24 |
| go1.28 은 아직 나오지 않았고 노트는 초안이다 | https://go.dev/doc/go1.28 | curl 로 받은 페이지의 h1 "Go 1.28 Release Notes", 릴리스 페이지에 go1.28 줄 없음 | 2026-09-24 |
