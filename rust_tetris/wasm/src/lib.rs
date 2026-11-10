//! 브라우저용 테트리스 — wasm-bindgen 없이 C ABI 함수 몇 개만 내보낸다.
//!
//! JS 와 WASM 사이에는 숫자(i32·i64·f32·f64)만 오갈 수 있다. 그래서
//! 상태는 Rust 쪽에 두고, JS 는 "입력 번호"를 넣고 "픽셀 버퍼의 주소"를
//! 받아 간다. 주소는 WASM 선형 메모리 안의 바이트 위치다.

use std::cell::RefCell;
use tetris_core::{Action, Game};
use tetris_render::{Frame, draw};

// ANCHOR: state
/// 탭 하나에 게임 하나. JS 쪽 함수 호출 사이에 살아 있어야 하니
/// 전역이어야 한다. `static mut` 은 2024 에디션에서 참조를 만들 수 없게
/// 막혔으므로(데이터 경쟁 위험) `thread_local!` + `RefCell` 을 쓴다.
/// WASM 은 스레드가 하나라 이 조합이 비용 없이 안전하다.
struct App {
    game: Game,
    frame: Frame,
    rgba: Vec<u8>, // 캔버스로 넘길 R·G·B·A 바이트. 한 번만 할당
    seed: u64,
}

thread_local! {
    static APP: RefCell<Option<App>> = const { RefCell::new(None) };
}

/// 상태가 있으면 `f` 를 돌리고, 아직 `tt_init` 전이면 `default`.
fn with_app<R>(default: R, f: impl FnOnce(&mut App) -> R) -> R {
    APP.with_borrow_mut(|app| match app {
        Some(a) => f(a),
        None => default,
    })
}
// ANCHOR_END: state

// ANCHOR: init
/// 새 판. 씨앗은 u64 인데 JS 의 Number 는 2⁵³ 까지만 정확하므로 32비트
/// 두 개로 받는다. `cell` 은 칸 한 변의 픽셀 수(8~64). 성공하면 1.
#[unsafe(no_mangle)]
pub extern "C" fn tt_init(
    seed_lo: u32,
    seed_hi: u32,
    cell: u32,
) -> u32 {
    if !(8..=64).contains(&cell) {
        return 0; // 패닉 대신 실패 값(extern "C" 밖 패닉은 abort)
    }
    let seed = (seed_hi as u64) << 32 | seed_lo as u64;
    let frame = Frame::new(cell as usize);
    let rgba = vec![0; frame.w * frame.h * 4];
    let app = App {
        game: Game::new(seed),
        frame,
        rgba,
        seed,
    };
    APP.with_borrow_mut(|slot| *slot = Some(app));
    1
}
// ANCHOR_END: init

// ANCHOR: input
/// 입력 번호 → 동작. 0~7 은 `Action`, 8 은 다시 시작(게임 오버 뒤만).
const ACTIONS: [Action; 8] = [
    Action::Left,
    Action::Right,
    Action::SoftDrop,
    Action::HardDrop,
    Action::RotateCw,
    Action::RotateCcw,
    Action::Hold,
    Action::Pause,
];

/// 무언가 바뀌었으면 1.
#[unsafe(no_mangle)]
pub extern "C" fn tt_input(code: u32) -> u32 {
    with_app(0, |a| {
        if code == 8 {
            if !a.game.is_over() {
                return 0;
            }
            a.seed = a.seed.wrapping_add(1);
            a.game = Game::new(a.seed);
            return 1;
        }
        match ACTIONS.get(code as usize) {
            Some(&act) => a.game.apply(act) as u32,
            None => 0,
        }
    })
}

#[unsafe(no_mangle)]
pub extern "C" fn tt_tick(dt_ms: u32) {
    with_app((), |a| a.game.tick(dt_ms));
}
// ANCHOR_END: input

// ANCHOR: render
/// 그린 뒤 RGBA 버퍼의 주소. `tt_init` 전이면 널(0).
///
/// 주소는 늘 같지만, JS 는 매번 `memory.buffer` 로 뷰를 새로 만들어야
/// 한다 — 메모리가 늘어나면(grow) 옛 ArrayBuffer 는 떨어져 나간다.
#[unsafe(no_mangle)]
pub extern "C" fn tt_render() -> *const u8 {
    with_app(std::ptr::null(), |a| {
        draw(&a.game, &mut a.frame);
        a.frame.write_rgba(&mut a.rgba);
        a.rgba.as_ptr()
    })
}

#[unsafe(no_mangle)]
pub extern "C" fn tt_width() -> u32 {
    with_app(0, |a| a.frame.w as u32)
}

#[unsafe(no_mangle)]
pub extern "C" fn tt_height() -> u32 {
    with_app(0, |a| a.frame.h as u32)
}

/// 0 점수 · 1 줄 · 2 레벨 · 3 게임 오버 · 4 일시정지. 모르는 번호는 0.
#[unsafe(no_mangle)]
pub extern "C" fn tt_stat(which: u32) -> u32 {
    with_app(0, |a| match which {
        0 => a.game.score(),
        1 => a.game.lines(),
        2 => a.game.level(),
        3 => a.game.is_over() as u32,
        4 => a.game.is_paused() as u32,
        _ => 0,
    })
}
// ANCHOR_END: render
