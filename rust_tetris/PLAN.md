# Rust 테트리스 덱 — 작업 계획과 진행 기록

산출물: 저장소 루트 `Rust_테트리스_만들기.html` (빌드 산출물 — 직접 고치지 말 것).
독자: Go·Java·Python·JS 숙련자. 덱은 `template.html` 엔진을 쓴다.

## 구성

| 크레이트 | 역할 | 의존성 |
|---|---|---|
| `core` | 규칙(판·조각·SRS·7-bag·점수·중력·고정 지연) | 없음 |
| `render` | 0RGB 픽셀 버퍼 렌더러 + 5×7 비트맵 글꼴 | core |
| `tui` | 터미널판 — 셀 버퍼 차분 그리기 | core, crossterm |
| `gui` | 데스크톱 창 | core, render, minifb |
| `wasm` | cdylib, 손으로 쓴 JS 글루 | core, render |

## 툴체인 (이 기계)

- core·render·tui·gui: proot Ubuntu `/usr/bin/cargo` 1.93 (`CARGO_BUILD_JOBS=1`).
  minifb 는 Termux 타깃(aarch64-linux-android)에서 컴파일되지 않는다.
- fmt·clippy: Termux `cargo fmt` / `cargo clippy` 1.99 (Ubuntu 에는 없다).
- wasm: Termux cargo 1.99 + `rust-std-wasm32-unknown-unknown`. 설치가 안 돼 있으면 .deb 를 풀어 만든
  사설 sysroot 를 `RUSTFLAGS=--sysroot=…` 로 준다(`make wasm`). 산출물 `out/tetris_wasm.wasm` 은 커밋한다.
- GUI 캡처: `tools/record_gui.sh` — Xvfb :77 + xdotool(XTEST 키) + xwd → magick PNG. Xvfb 는 trap 으로 kill.

## 진행 기록 (최신이 위)

- 2026-11-10 덱 완성: 5부 11장 191장. `make all WASM_SYSROOT=…` 초록(시험 81 + node 8, 검사 232).
  build.py 의 72칸·45줄 제한에 맞춰 소스 주석·JS 글루·node 시험을 다시 접었고(동작 불변, 재시험),
  긴 앵커는 둘로 나눴다(bag→bag/bag_draw, mount→mount/frame). wasm 은 bag.rs 줄 이동으로 해시만 바뀜(33,332 B 그대로).
  sysroot 는 `WASM_SYSROOT` 로 wasm 빌드에만 — RUSTFLAGS 를 통째로 주면 Ubuntu cargo 가 E0463 으로 깨진다.
  `make deck` 이 DeckMono 내장까지 한다.
- 2026-11-10 wasm: 33 KB, import 0. node 시험 8 통과. wasm 타깃은 사설 sysroot 로(메모리 노트 참고).
- 2026-11-10 render 11 · tui 10 · gui 5 · wasm(ffi) 7 시험 RED→GREEN. TUI 는 tmux, GUI 는 Xvfb+xdotool 로 실제 실행 캡처.
- 2026-11-10 core: 시험 47개 먼저(RED 47 실패 확인) → 구현 → 47 + doctest 1 통과, clippy 0.
- 2026-11-10 착수. 워크스페이스 뼈대.
