//! 터미널 테트리스.
//!
//!     cargo run -p tetris-tui --release [-- --seed 42]
//!
//! 키: ← → 이동 · ↓ 소프트 드롭 · ↑/X 시계 회전 · Z 반시계 · Space 하드 드롭
//!     C 홀드 · P/Esc 일시정지 · R 다시 시작(게임 오버 뒤) · Q 끝내기

use crossterm::event::{self, Event};
use crossterm::{cursor, execute, terminal};
use std::io::{self, BufWriter, stdout};
use std::time::{Duration, Instant, SystemTime, UNIX_EPOCH};
use tetris_core::Game;
use tetris_tui::{
    Command, H, Screen, W, compose, key_to_command, present,
};

// ANCHOR: guard
/// 터미널을 되돌리는 경비원. 만들 때 raw 모드·대체 화면에 들어가고,
/// 버려질 때(`Drop`) 원래대로 돌린다 — `?` 로 일찍 빠져나가도, 패닉으로
/// 스택이 풀려도. Go 의 `defer`, Java 의 try-with-resources 자리다.
struct TerminalGuard;

impl TerminalGuard {
    fn enter() -> io::Result<TerminalGuard> {
        terminal::enable_raw_mode()?;
        execute!(
            stdout(),
            terminal::EnterAlternateScreen,
            cursor::Hide
        )?;
        Ok(TerminalGuard)
    }
}

impl Drop for TerminalGuard {
    fn drop(&mut self) {
        // drop 은 실패를 돌려줄 수 없다. 되돌리기는 최선을 다할 뿐.
        let _ = execute!(
            stdout(),
            cursor::Show,
            terminal::LeaveAlternateScreen
        );
        let _ = terminal::disable_raw_mode();
    }
}
// ANCHOR_END: guard

// ANCHOR: seed
/// `--seed N` 이 있으면 그 값, 없으면 현재 시각(나노초).
fn seed_from_args() -> Result<u64, String> {
    let args: Vec<String> = std::env::args().skip(1).collect();
    match args.as_slice() {
        [] => Ok(SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .map(|d| d.as_nanos() as u64)
            .unwrap_or(0)),
        [flag, n] if flag == "--seed" => {
            n.parse().map_err(|e| format!("--seed {n}: {e}"))
        }
        _ => Err("쓰는 법: tetris-tui [--seed N]".into()),
    }
}
// ANCHOR_END: seed

// ANCHOR: main
fn main() -> io::Result<()> {
    let seed = match seed_from_args() {
        Ok(s) => s,
        Err(msg) => {
            eprintln!("{msg}");
            std::process::exit(2);
        }
    };
    let (cols, rows) = terminal::size()?;
    if (cols as usize) < W || (rows as usize) < H {
        eprintln!(
            "터미널이 {W}×{H} 이상이어야 한다(지금 {cols}×{rows})"
        );
        std::process::exit(1);
    }

    let mut game = Game::new(seed);
    let _guard = TerminalGuard::enter()?; // 어떻게 끝나도 복구
    let mut out = BufWriter::new(stdout());
    let mut prev: Option<Screen> = None;
    let mut last = Instant::now();
    let frame = Duration::from_millis(16);

    loop {
        // 입력: 한 프레임만큼 기다리고, 쌓인 이벤트는 기다리지 않고 비운다
        let mut wait = frame;
        while event::poll(wait)? {
            wait = Duration::ZERO;
            match event::read()? {
                Event::Key(k) => match key_to_command(k) {
                    Some(Command::Quit) => return Ok(()),
                    Some(Command::Restart) if game.is_over() => {
                        game = Game::new(seed.wrapping_add(1));
                    }
                    Some(Command::Play(a)) => {
                        game.apply(a);
                    }
                    _ => {}
                },
                Event::Resize(..) => prev = None, // 전부 다시 그린다
                _ => {}
            }
        }

        // 시간: 지난 ms 만큼 흘려보내고, 1ms 미만 나머지는 다음 번으로
        let ms = last.elapsed().as_millis() as u32;
        last += Duration::from_millis(ms as u64);
        game.tick(ms);

        let next = compose(&game);
        present(&mut out, prev.as_ref(), &next)?;
        prev = Some(next);
    }
}
// ANCHOR_END: main
