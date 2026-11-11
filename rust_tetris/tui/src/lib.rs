//! 터미널 화면 합성 — 순수 함수만 둔다(터미널 없이 시험 가능).
//!
//! 흐름: `Game` → `compose` → `Screen`(글자 격자) → 이전 화면과 `diff`
//! → 바뀐 칸만 `present` 로 터미널에 쓴다. 웹의 가상 DOM 과 같다.

use crossterm::cursor::MoveTo;
use crossterm::event::{KeyCode, KeyEvent, KeyEventKind, KeyModifiers};
use crossterm::queue;
use crossterm::style::{Color, Colors, Print, ResetColor, SetColors};
use crossterm::terminal::{Clear, ClearType};
use std::io::{self, Write};
use tetris_core::{Action, Game, HEIGHT, Kind, WIDTH};

/// 화면 크기(글자). 판 22열 + 틈 2 + 패널 16 = 40열, 판 21행 + 도움말 2.
pub const W: usize = 40;
pub const H: usize = 23;
const PANEL_X: usize = 24;

// ANCHOR: screen
/// 글자 한 칸.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Cell {
    pub ch: char,
    pub fg: Color,
    pub bg: Color,
}

const BLANK: Cell = Cell {
    ch: ' ',
    fg: Color::Reset,
    bg: Color::Reset,
};

/// W×H 글자 격자. 1차원 `Vec` 에 행 우선으로 담는다(번호 = y×W + x).
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Screen {
    cells: Vec<Cell>,
}

impl Default for Screen {
    fn default() -> Self {
        Screen::new()
    }
}

impl Screen {
    pub fn new() -> Screen {
        Screen {
            cells: vec![BLANK; W * H],
        }
    }

    pub fn get(&self, x: usize, y: usize) -> Cell {
        self.cells[y * W..(y + 1) * W][x]
    }

    fn set(&mut self, x: usize, y: usize, cell: Cell) {
        if x < W && y < H {
            self.cells[y * W + x] = cell;
        }
    }

    /// 화면 밖으로 나가는 글자는 버린다(패닉하지 않는다).
    pub fn put_str(
        &mut self,
        x: usize,
        y: usize,
        s: &str,
        fg: Color,
        bg: Color,
    ) {
        for (i, ch) in s.chars().enumerate() {
            self.set(x + i, y, Cell { ch, fg, bg });
        }
    }

    /// 한 행의 글자만(색 없이). 시험과 녹화에 쓴다.
    pub fn row_text(&self, y: usize) -> String {
        self.cells[y * W..(y + 1) * W]
            .iter()
            .map(|c| c.ch)
            .collect()
    }
}
// ANCHOR_END: screen

// ANCHOR: keys
/// 키가 하는 일. 게임 입력 외에 "다시 시작"과 "끝내기"가 있다.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Command {
    Play(Action),
    Restart,
    Quit,
}

pub fn key_to_command(key: KeyEvent) -> Option<Command> {
    // 윈도 콘솔은 누를 때와 뗄 때 두 번 보낸다. 뗄 때는 버린다.
    if key.kind == KeyEventKind::Release {
        return None;
    }
    // raw 모드에서는 Ctrl+C 가 시그널이 아니라 그냥 키로 온다
    let ctrl = key.modifiers.contains(KeyModifiers::CONTROL);
    if ctrl && key.code == KeyCode::Char('c') {
        return Some(Command::Quit);
    }
    let a = match key.code {
        KeyCode::Left => Action::Left,
        KeyCode::Right => Action::Right,
        KeyCode::Down => Action::SoftDrop,
        KeyCode::Up => Action::RotateCw,
        KeyCode::Char(' ') => Action::HardDrop,
        KeyCode::Esc => Action::Pause,
        KeyCode::Char(c) => match c.to_ascii_lowercase() {
            'x' => Action::RotateCw,
            'z' => Action::RotateCcw,
            'c' => Action::Hold,
            'p' => Action::Pause,
            'r' => return Some(Command::Restart),
            'q' => return Some(Command::Quit),
            _ => return None,
        },
        _ => return None,
    };
    Some(Command::Play(a))
}
// ANCHOR_END: keys

// ANCHOR: compose
fn rgb(c: u32) -> Color {
    Color::Rgb {
        r: (c >> 16) as u8,
        g: (c >> 8) as u8,
        b: c as u8,
    }
}

/// 게임 상태 → 글자 격자. 색 표는 픽셀 렌더러의 것을 같이 쓴다.
pub fn compose(game: &Game) -> Screen {
    use tetris_render::{BOARD_BG, OVERLAY, color};
    let mut s = Screen::new();
    let (board_bg, dot) = (rgb(BOARD_BG), rgb(0x3A_4258));

    // 판: 한 칸 = 글자 2개. 정사각형에 가깝게 보이려고.
    for y in 0..HEIGHT {
        s.put_str(0, y, "|", Color::Reset, Color::Reset);
        for x in 0..WIDTH {
            let cell = game.board().get(x as i32, y as i32);
            match cell {
                Some(k) => s.put_str(
                    1 + x * 2,
                    y,
                    "  ",
                    board_bg,
                    rgb(color(k)),
                ),
                None => s.put_str(1 + x * 2, y, " .", dot, board_bg),
            }
        }
        s.put_str(1 + WIDTH * 2, y, "|", Color::Reset, Color::Reset);
    }
    let bottom = format!("+{}+", "-".repeat(WIDTH * 2));
    s.put_str(0, HEIGHT, &bottom, Color::Reset, Color::Reset);

    if !game.is_over() {
        let ghost = game.ghost();
        for (x, y) in ghost.cells() {
            if y >= 0 {
                let fg = rgb(color(ghost.kind));
                s.put_str(
                    1 + x as usize * 2,
                    y as usize,
                    "[]",
                    fg,
                    board_bg,
                );
            }
        }
        let cur = game.current();
        for (x, y) in cur.cells() {
            if y >= 0 {
                let bg = rgb(color(cur.kind));
                s.put_str(
                    1 + x as usize * 2,
                    y as usize,
                    "  ",
                    board_bg,
                    bg,
                );
            }
        }
    }

    panel(game, &mut s);
    s.put_str(
        0,
        21,
        "<- -> v move  ^ x cw  z ccw",
        Color::Reset,
        Color::Reset,
    );
    s.put_str(
        0,
        22,
        "space drop  c hold  p pause  q quit",
        Color::Reset,
        Color::Reset,
    );

    if game.is_over() || game.is_paused() {
        let (msg, hint) = if game.is_over() {
            ("GAME OVER", "r retry")
        } else {
            ("PAUSED", "p resume")
        };
        let ov = rgb(OVERLAY);
        for y in 9..=11 {
            s.put_str(1, y, &" ".repeat(WIDTH * 2), Color::Reset, ov);
        }
        let mid = |t: &str| 1 + (WIDTH * 2 - t.len()) / 2;
        s.put_str(mid(msg), 10, msg, Color::White, ov);
        s.put_str(mid(hint), 11, hint, Color::Grey, ov);
    }
    s
}

/// 패널에 조각 모양 하나. I 처럼 상자 둘째 줄에서 시작하는 모양도
/// 맨 윗줄에 붙도록 가장 작은 y 를 뺀다.
fn mini(s: &mut Screen, x: usize, y: usize, kind: Kind) {
    let cells = kind.spawn_cells();
    let top = cells.iter().map(|c| c.1).min().unwrap_or(0);
    let bg = rgb(tetris_render::color(kind));
    for (cx, cy) in cells {
        s.put_str(
            x + cx as usize * 2,
            y + (cy - top) as usize,
            "  ",
            Color::Reset,
            bg,
        );
    }
}

fn panel(game: &Game, s: &mut Screen) {
    let label = |s: &mut Screen, y, t: &str| {
        s.put_str(PANEL_X, y, t, Color::DarkGrey, Color::Reset);
    };
    label(s, 0, "NEXT");
    for (i, k) in game.next_kinds().take(3).enumerate() {
        mini(s, PANEL_X, 1 + i * 3, k);
    }
    label(s, 10, "HOLD");
    if let Some(k) = game.hold() {
        mini(s, PANEL_X, 11, k);
    }
    let stats = [
        ("SCORE", game.score()),
        ("LINES", game.lines()),
        ("LEVEL", game.level()),
    ];
    for (i, (name, v)) in stats.into_iter().enumerate() {
        label(s, 14 + i * 2, name);
        s.put_str(
            PANEL_X,
            15 + i * 2,
            &v.to_string(),
            Color::Reset,
            Color::Reset,
        );
    }
}
// ANCHOR_END: compose

// ANCHOR: diff
/// 바뀐 칸 번호들. 두 화면은 언제나 W×H 다(필드가 비공개).
pub fn diff(prev: &Screen, next: &Screen) -> Vec<usize> {
    prev.cells
        .iter()
        .zip(&next.cells)
        .enumerate()
        .filter(|(_, (a, b))| a != b)
        .map(|(i, _)| i)
        .collect()
}

/// 터미널에 쓴다. `prev` 가 없으면(첫 화면·창 크기 변경) 전부 그린다.
///
/// 커서가 이미 그 자리에 있으면 `MoveTo` 를, 색이 같으면 `SetColors` 를
/// 생략한다. `queue!` 는 버퍼에 쌓기만 하고 `flush` 때 한 번에 나간다.
pub fn present(
    out: &mut impl Write,
    prev: Option<&Screen>,
    next: &Screen,
) -> io::Result<()> {
    let changed: Vec<usize> = match prev {
        Some(p) => diff(p, next),
        None => {
            queue!(out, Clear(ClearType::All))?;
            (0..W * H).collect()
        }
    };
    if changed.is_empty() {
        return out.flush();
    }
    let mut cursor: Option<usize> = None;
    let mut colors: Option<(Color, Color)> = None;
    for i in changed {
        let c = next.cells[i];
        if cursor != Some(i) {
            queue!(out, MoveTo((i % W) as u16, (i / W) as u16))?;
        }
        if colors != Some((c.fg, c.bg)) {
            queue!(out, SetColors(Colors::new(c.fg, c.bg)))?;
            colors = Some((c.fg, c.bg));
        }
        queue!(out, Print(c.ch))?;
        // 행 끝에서는 커서가 다음 행으로 가지 않는다(터미널이 더 넓다)
        cursor = if i % W + 1 < W { Some(i + 1) } else { None };
    }
    queue!(out, ResetColor)?;
    out.flush()
}
// ANCHOR_END: diff
