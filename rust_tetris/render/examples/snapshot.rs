//! 창 없이 한 프레임을 PPM 파일로 저장한다.
//!
//!     cargo run -p tetris-render --example snapshot -- out.ppm
//!
//! PPM(P6)은 머리말 한 줄 + RGB 바이트라 라이브러리 없이 쓸 수 있다.
use std::io::Write;
use tetris_core::{Action, Game};
use tetris_render::{Frame, draw};

fn main() -> std::io::Result<()> {
    let path = std::env::args().nth(1).unwrap_or("snapshot.ppm".into());
    let mut g = Game::new(2026);
    // 정해진 입력열로 몇 조각 쌓는다 — 씨앗이 같으면 그림도 같다
    let script = [
        Action::Left,
        Action::Left,
        Action::Left,
        Action::HardDrop,
        Action::RotateCw,
        Action::Right,
        Action::Right,
        Action::Right,
        Action::HardDrop,
        Action::HardDrop,
        Action::Hold,
        Action::RotateCcw,
        Action::Left,
        Action::HardDrop,
    ];
    for a in script {
        g.apply(a);
    }
    g.tick(3000);
    let mut f = Frame::new(24);
    draw(&g, &mut f);

    let mut out = std::fs::File::create(&path)?;
    write!(out, "P6\n{} {}\n255\n", f.w, f.h)?;
    let mut rgb = Vec::with_capacity(f.w * f.h * 3);
    for p in &f.px {
        rgb.extend_from_slice(&[
            (p >> 16) as u8,
            (p >> 8) as u8,
            *p as u8,
        ]);
    }
    out.write_all(&rgb)?;
    println!("{path}: {}×{}", f.w, f.h);
    Ok(())
}
