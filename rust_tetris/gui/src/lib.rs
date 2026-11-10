//! 키 배치 — 창을 열지 않고 시험할 수 있게 main 에서 떼어 냈다.

use minifb::{Key, KeyRepeat};
use tetris_core::Action;

// ANCHOR: bindings
/// (키, 누르고 있을 때 반복하나, 동작). 이동은 반복, 회전·드롭은 한 번.
/// `&[...]` 는 정적 슬라이스 — 프로그램 수명 내내 있는 상수 표다.
pub const BINDINGS: &[(Key, KeyRepeat, Action)] = &[
    (Key::Left, KeyRepeat::Yes, Action::Left),
    (Key::Right, KeyRepeat::Yes, Action::Right),
    (Key::Down, KeyRepeat::Yes, Action::SoftDrop),
    (Key::Up, KeyRepeat::No, Action::RotateCw),
    (Key::X, KeyRepeat::No, Action::RotateCw),
    (Key::Z, KeyRepeat::No, Action::RotateCcw),
    (Key::Space, KeyRepeat::No, Action::HardDrop),
    (Key::C, KeyRepeat::No, Action::Hold),
    (Key::P, KeyRepeat::No, Action::Pause),
    (Key::Escape, KeyRepeat::No, Action::Pause),
];

/// 이번 프레임에 눌린 키들의 동작. `pressed` 는 보통
/// `|k, r| window.is_key_pressed(k, r)` 이고, 시험에서는 가짜 함수다.
pub fn actions(
    pressed: impl Fn(Key, KeyRepeat) -> bool,
) -> Vec<Action> {
    BINDINGS
        .iter()
        .filter(|(k, r, _)| pressed(*k, *r))
        .map(|(_, _, a)| *a)
        .collect()
}
// ANCHOR_END: bindings
