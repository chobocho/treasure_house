# 수학적 최적화 완전 가이드 — 작업 계획

> 산출물: 저장소 루트의 `수학적_최적화_완전_가이드.html` (단일 파일 슬라이드 덱)
> 목표 분량: 14부 · 620장 이상

## 규율

1. **덱을 직접 고치지 않는다.** 항상 `optim/deck/sections/*.html` 을 고치고 다시 빌드한다.
2. **덱에 손으로 쓴 코드를 넣지 않는다.** 코드는 `data-src`+`data-sym` 으로 실제 파일을 가리키고,
   빌더가 그 줄을 읽어 채운다. 실행 출력은 `data-out` 으로 `out/manifest.json` 을 가리킨다.
3. **테스트를 먼저 쓴다.** 구현 전에 `tests/` 에 실패하는 테스트가 있어야 한다.
4. **고정폭 블록에는 괘선 문자(─ │ ┌)를 쓰지 않는다.** 폴드7 글꼴에서 폭이 어긋난다.
   표 구분선은 ASCII 하이픈(`fmt.table`).
5. 순수 파이썬 표준 라이브러리만 쓴다. numpy·scipy 금지.

## 빌드

```sh
cd optim
python3 -m unittest discover -s tests -t . -q   # 전체 테스트
cd .. && python3 optim/run_all.py               # 데모 실행 → out/manifest.json
python3 optim/deck/build_deck.py                # 덱 조립
python3 optim/deck/verify_deck.py               # 덱 ↔ 소스 역검증
```

## 부 구성과 진행

| 부 | 제목 | 목표 장수 | 상태 |
|---|---|---|---|
| 앞 | 표지·서문 | 11 | ✅ |
| 1 | 준비 — 최적화의 언어 | 42 | ✅ 40장 |
| 2 | 볼록성 | 42 | ✅ 33장 |
| 3 | 무제약 최적화 | 60 | ✅ 46장 |
| 4 | 최소제곱과 회귀 | 40 | ✅ 22장 |
| 5 | 제약 최적화와 쌍대성 | 55 | ✅ 30장 |
| 6 | 선형계획법 | 50 | ⬜ |
| 7 | 정수·조합 최적화 | 50 | ⬜ |
| 8 | 확률적·대규모 최적화 | 55 | ⬜ |
| 9 | 비평활·전역 최적화 | 40 | ⬜ |
| 10 | 프로세스 마이닝 ① 로그와 발견 | 55 | ⬜ |
| 11 | 프로세스 마이닝 ② 적합도와 정렬 | 50 | ⬜ |
| 12 | 프로세스 마이닝 ③ 성능·개선 | 45 | ⬜ |
| 13 | 응용 — 정식화 연습 | 35 | ⬜ |
| 14 | 마무리 | 25 | ⬜ |

## 진행 로그

### [2026-09-04] 뼈대
- **기획:** template.html 기반 단일 파일 덱 + hexwar 식 소스 인용 빌드 파이프라인.
  수식은 외부 라이브러리 없이 CSS 키트(분수·큰 연산자·행렬·경우나눔·정리 상자)로 조판.
- **TC:** `tests/test_linalg.py`(24) · `test_numdiff.py`(14) · `test_fmt.py`(4) 를 구현보다 먼저 작성, RED 확인.
- **개발:** `py/linalg.py` `py/numdiff.py` `py/funcs.py` `py/fmt.py`,
  `deck/base/head.html`(수식 CSS 포함) `deck/build_deck.py` `deck/verify_deck.py` `run_all.py`,
  `deck/sections/00-front.html`(11장).
- **검증:** 42 passed, 0 failed. 데모 2개 실행 성공. 덱 빌드 11장, 역검증 문제 0건.

### [2026-09-04] 1부 — 준비
- **기획:** 표준형·존재성(바이어슈트라스·강제성) → 선형대수(코시–슈바르츠·레일리·조건수·SVD)
  → 다변수 미적분(최급강하·테일러·하강 보조정리) → 수치의 현실(최적 차분 스텝·복소 스텝).
- **TC:** `test_fmt.py` 4개 추가(한글·결합문자 폭). 전체 42 passed.
- **개발:** `deck/sections/01-prep.html`(40장), `py/demo_linalg.py` `py/demo_numdiff.py`
  `py/fmt.py`, `deck/demos.js`(방향도함수 탐색기).
- **검증:** 42 passed / 0 failed. 덱 51장, 코드 인용 11블록, 실행 출력 2개, 역검증 0건.
- **비고:** 증명 12건 수록. 괘선 문자 대신 ASCII 하이픈 규칙을 `fmt.table` 에 고정.

### [2026-09-04] 2부 — 볼록성
- **기획:** 볼록집합(투영·분리·원뿔) → 볼록함수(젠센·1차/2차 판정·강볼록·열경사·켤레)
  → 볼록 최적화의 힘(국소=전역·유일성·변분 부등식) → 비볼록의 함정.
- **TC:** `test_convex.py` 17개(젠센 반례 탐지, 단체 투영이 최단·비확장, 열경사 부등식).
- **개발:** `py/convex.py` `py/demo_convex.py`, `deck/sections/02-convex.html`(33장),
  `deck/demos.js` 에 젠센 시각화 데모 추가.
- **검증:** 59 passed / 0 failed. 덱 84장, 역검증 0건.
- **비고:** 증명 17건. 단체 투영의 유도는 5부 KKT 를 앞당겨 썼다고 본문에 명시.

### [2026-09-04] 3부 — 무제약 최적화
- **기획:** 최적성 조건 → 경사하강 수렴 정리 4종 → 라인서치(Armijo·Wolfe·Zoutendijk)
  → 뉴턴(이차수렴 증명) → 준뉴턴(BFGS 정부호 유지) → CG·신뢰영역 → 자동미분.
- **TC:** `test_unconstrained.py` 22개(발산 경계 2/L, 수렴 인자 (k-1)/(k+1) 8자리 일치,
  CG n회 유한 종료, 뉴턴 이차수렴, f 단조 감소), `test_autodiff.py` 10개.
- **개발:** `py/unconstrained.py` `py/autodiff.py`, 데모 7종(`demo_gd/methods/newton/cg/
  lbfgs/linesearch/autodiff.py`), `deck/sections/03-uncon.html`(46장), 경사하강 궤적 데모.
- **검증:** 91 passed / 0 failed. 덱 130장, 코드 인용 25블록, 실행 출력 10개, 역검증 0건.
- **비고:** 증명 20건. funcs.py 의 math.fsum 을 자동미분 대응 fsum 으로 교체(형 디스패치).
  Rosenbrock 의 기본 출발점을 관례적인 교대 형태로 정정(그 전 값은 n>=4 에서 국소해로 빠졌다).

### [2026-09-04] 4부 — 최소제곱과 회귀
- **기획:** 정규방정식의 기하(정사영) → 조건수 제곱 정리 → SVD 최소노름해 → 릿지의
  스펙트럼 필터 → 라쏘 희소성의 열경사 근거 → GN/LM → 기저·가중·로버스트·CGLS.
- **TC:** `test_leastsq.py` 20개(세 해법 일치, QR 이 정규방정식을 이기는 지점,
  최소노름 해, 릿지=SVD 필터, 원 맞추기, 후버가 이상치에 버팀, CGLS).
- **개발:** `py/leastsq.py`, `py/demo_leastsq.py` `py/demo_lsq2.py`,
  `deck/sections/04-lsq.html`(22장), 곡선 맞추기 데모.
- **검증:** 111 passed / 0 failed. 덱 152장, 역검증 0건.
- **비고:** 증명 10건. CGLS 는 A^T A 를 만들지 않는 구현으로 다시 작성했다.

### [2026-09-04] 5부 — 제약 최적화와 쌍대성
- **기획:** 등식 제약(음함수 정리로 라그랑주 유도·감도 정리) → 부등식(Farkas 로 KKT 증명)
  → 쌍대성(약/강, Slater 를 분리 정리로) → 알고리즘(투영·페널티·ALM·배리어).
- **TC:** `test_constrained.py` 15개(승수=감도 수치 확인, KKT 잔차 4종, 투영경사 고정점,
  페널티는 늘 위반·ALM 은 같은 μ 에서 10^8배 정확, 쌍대함수의 오목성).
- **개발:** `py/constrained.py` `py/demo_constrained.py`, `deck/sections/05-kkt.html`(30장).
- **검증:** 126 passed / 0 failed. 덱 182장, 역검증 0건.
- **비고:** 증명 15건. ALM 의 μ 증가 규칙에 ctol 을 두어 위반이 수치 바닥에 닿은 뒤
  μ 가 무한정 커지는 버그를 잡았다(그 상태에서 ν += μh 가 반올림을 증폭했다).
