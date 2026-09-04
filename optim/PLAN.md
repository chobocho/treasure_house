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
| 1 | 준비 — 최적화의 언어 | 42 | ⬜ |
| 2 | 볼록성 | 42 | ⬜ |
| 3 | 무제약 최적화 | 60 | ⬜ |
| 4 | 최소제곱과 회귀 | 40 | ⬜ |
| 5 | 제약 최적화와 쌍대성 | 55 | ⬜ |
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
