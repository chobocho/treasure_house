//! 데스크톱 창 테트리스 (Windows · macOS · Linux/X11).
//!
//!     cargo run -p tetris-gui --release [-- --seed 42]
//!
//! 키: ← → ↓ 이동 · ↑/X 시계 회전 · Z 반시계 · Space 하드 드롭 · C 홀드
//!     P/Esc 일시정지 · R 다시 시작(게임 오버 뒤) · Q 끝내기

use minifb::{Key, KeyRepeat, Window, WindowOptions};
use std::time::{Duration, Instant, SystemTime, UNIX_EPOCH};
use tetris_core::Game;
use tetris_gui::actions;
use tetris_render::{Frame, draw};

fn seed_from_args() -> u64 {
    let mut args = std::env::args().skip(1);
    match (args.next().as_deref(), args.next()) {
        (Some("--seed"), Some(n)) => n.parse().unwrap_or_else(|e| {
            eprintln!("--seed {n}: {e}");
            std::process::exit(2);
        }),
        _ => SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .map(|d| d.as_nanos() as u64)
            .unwrap_or(0),
    }
}

// ANCHOR: main
fn main() {
    let seed = seed_from_args();
    let mut game = Game::new(seed);
    let mut frame = Frame::new(28); // 칸 28px → 창 462×588

    let opts = WindowOptions::default();
    let mut win = Window::new("Rust 테트리스", frame.w, frame.h, opts)
        .unwrap_or_else(|e| {
            eprintln!("창을 열 수 없다: {e}");
            std::process::exit(1);
        });
    win.set_target_fps(60); // update_with_buffer 가 알아서 쉬어 준다
    win.set_key_repeat_delay(0.17); // 첫 반복까지 170ms
    win.set_key_repeat_rate(0.05); //  그 뒤 50ms 마다

    let mut last = Instant::now();
    while win.is_open() && !win.is_key_down(Key::Q) {
        for a in actions(|k, r| win.is_key_pressed(k, r)) {
            game.apply(a);
        }
        if game.is_over() && win.is_key_pressed(Key::R, KeyRepeat::No) {
            game = Game::new(seed.wrapping_add(1));
        }

        let ms = last.elapsed().as_millis() as u32;
        last += Duration::from_millis(ms as u64);
        game.tick(ms);

        draw(&game, &mut frame);
        // 버퍼를 창에 올리고, 그동안 들어온 키·마우스 이벤트를 모은다
        if let Err(e) =
            win.update_with_buffer(&frame.px, frame.w, frame.h)
        {
            eprintln!("그리기 실패: {e}");
            break;
        }
    }
}
// ANCHOR_END: main
