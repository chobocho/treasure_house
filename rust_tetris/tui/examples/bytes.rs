//! 전부 다시 그릴 때와 바뀐 칸만 그릴 때 터미널로 나가는 바이트를 잰다.
//!     cargo run -p tetris-tui --example bytes
use tetris_core::{Action, Game};
use tetris_tui::{H, W, compose, diff, present};

fn main() -> std::io::Result<()> {
    let mut g = Game::new(7);
    let a = compose(&g);
    let mut full = Vec::new();
    present(&mut full, None, &a)?;

    let cases = [
        ("오른쪽 한 칸", Action::Right),
        ("회전", Action::RotateCw),
        ("하드 드롭", Action::HardDrop),
    ];
    // 한글은 2칸이라 {:<14} 로는 줄이 안 맞는다 → 이름을 끝에
    println!("{:>5}{:>8}  경우", "cells", "bytes");
    println!("{:>5}{:>8}  첫 화면(전부)", W * H, full.len());
    let mut prev = a;
    for (name, act) in cases {
        g.apply(act);
        let next = compose(&g);
        let mut out = Vec::new();
        present(&mut out, Some(&prev), &next)?;
        let n = diff(&prev, &next).len();
        println!("{n:>5}{:>8}  {name}", out.len());
        prev = next;
    }
    Ok(())
}
