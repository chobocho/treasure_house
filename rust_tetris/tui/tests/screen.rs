// TUI 화면 합성·차분·키 매핑 시험 — 터미널을 열지 않는다.
use crossterm::event::{KeyCode, KeyEvent, KeyEventKind, KeyModifiers};
use crossterm::style::Color;
use tetris_core::{Action, Board, Game, Kind};
use tetris_tui::{
    Command, H, Screen, W, compose, diff, key_to_command, present,
};

fn game(rows: &[&str], queue: &[Kind]) -> Game {
    Game::with_setup(Board::from_rows(rows), queue, 1)
}

fn rgb(c: u32) -> Color {
    Color::Rgb {
        r: (c >> 16) as u8,
        g: (c >> 8) as u8,
        b: c as u8,
    }
}

/// 판 칸 (x, y) 의 왼쪽 글자. 판은 1열부터, 한 칸이 2글자.
fn board_cell(s: &Screen, x: usize, y: usize) -> (char, char, Color) {
    let a = s.get(1 + x * 2, y);
    let b = s.get(2 + x * 2, y);
    (a.ch, b.ch, a.bg)
}

fn press(code: KeyCode) -> KeyEvent {
    KeyEvent::new(code, KeyModifiers::NONE)
}

#[test]
fn new_screen_is_blank() {
    let s = Screen::new();
    for y in 0..H {
        assert_eq!(s.row_text(y), " ".repeat(W));
    }
}

#[test]
fn put_str_clips_at_the_right_edge() {
    let mut s = Screen::new();
    s.put_str(W - 2, 0, "hello", Color::Reset, Color::Reset);
    assert!(s.row_text(0).ends_with("he"));
    s.put_str(0, H + 5, "x", Color::Reset, Color::Reset); // 화면 밖: 무시
}

#[test]
fn piece_ghost_and_empty_cells() {
    let s = compose(&game(&[], &[Kind::T]));
    let t = rgb(tetris_render::color(Kind::T));
    assert_eq!(
        board_cell(&s, 4, 0),
        (' ', ' ', t),
        "조각은 배경색 두 칸"
    );
    let (a, b, _) = board_cell(&s, 3, 19);
    assert_eq!((a, b), ('[', ']'), "그림자");
    let (a, b, _) = board_cell(&s, 0, 10);
    assert_eq!((a, b), (' ', '.'), "빈 칸");
}

#[test]
fn borders_are_ascii() {
    let s = compose(&Game::new(1));
    assert_eq!(s.get(0, 5).ch, '|');
    assert_eq!(s.get(21, 5).ch, '|');
    assert!(s.row_text(20).starts_with("+--------------------+"));
    for y in 0..H {
        assert!(s.row_text(y).is_ascii(), "{y}행에 ASCII 아닌 글자");
    }
}

#[test]
fn panel_shows_labels_and_values() {
    let mut g = game(&[], &[Kind::T, Kind::O]);
    g.apply(Action::HardDrop);
    let s = compose(&g);
    let all: Vec<String> = (0..H).map(|y| s.row_text(y)).collect();
    let text = all.join("\n");
    for label in ["NEXT", "HOLD", "SCORE", "LINES", "LEVEL", "q quit"] {
        assert!(text.contains(label), "{label} 없음");
    }
    let score_row =
        all.iter().position(|r| r.contains("SCORE")).unwrap();
    assert!(all[score_row + 1].contains("36"));
}

#[test]
fn overlays() {
    let mut rows = vec![".........."; 20];
    rows[1] = "...LLL....";
    let s = compose(&game(&rows, &[Kind::T]));
    assert!(s.row_text(10).contains("GAME OVER"));
    assert!(
        s.row_text(10).contains("r retry")
            || s.row_text(11).contains("r retry")
    );

    let mut g = Game::new(1);
    g.apply(Action::Pause);
    assert!(compose(&g).row_text(10).contains("PAUSED"));
}

#[test]
fn diff_finds_only_changed_cells() {
    let mut g = game(&[], &[Kind::T]);
    let a = compose(&g);
    assert!(diff(&a, &a).is_empty());
    g.apply(Action::Right);
    let b = compose(&g);
    let d = diff(&a, &b);
    assert!(!d.is_empty());
    assert!(d.contains(&(W + 1 + 3 * 2))); // (3,1) 칸: T 가 떠난 자리
    assert!(d.len() < W * H / 4, "일부만 바뀐다: {}", d.len());
}

#[test]
fn present_full_then_incremental() {
    let mut g = game(&[], &[Kind::T]);
    let a = compose(&g);
    let mut out = Vec::new();
    present(&mut out, None, &a).unwrap();
    let first = String::from_utf8(out).unwrap();
    assert!(first.contains("\x1b[2J"), "첫 화면은 지우고 전부 그린다");
    assert!(first.contains("NEXT"));

    let mut out = Vec::new();
    present(&mut out, Some(&a), &a).unwrap();
    assert!(
        out.len() < 16,
        "바뀐 게 없으면 거의 안 쓴다: {}",
        out.len()
    );

    g.apply(Action::Right);
    let b = compose(&g);
    let mut out = Vec::new();
    present(&mut out, Some(&a), &b).unwrap();
    let inc = String::from_utf8(out).unwrap();
    assert!(!inc.contains("\x1b[2J"));
    assert!(inc.len() < first.len() / 4);
}

#[test]
fn key_mapping() {
    use Command::*;
    let cases = [
        (KeyCode::Left, Some(Play(Action::Left))),
        (KeyCode::Right, Some(Play(Action::Right))),
        (KeyCode::Down, Some(Play(Action::SoftDrop))),
        (KeyCode::Up, Some(Play(Action::RotateCw))),
        (KeyCode::Char('x'), Some(Play(Action::RotateCw))),
        (KeyCode::Char('X'), Some(Play(Action::RotateCw))),
        (KeyCode::Char('z'), Some(Play(Action::RotateCcw))),
        (KeyCode::Char(' '), Some(Play(Action::HardDrop))),
        (KeyCode::Char('c'), Some(Play(Action::Hold))),
        (KeyCode::Char('p'), Some(Play(Action::Pause))),
        (KeyCode::Esc, Some(Play(Action::Pause))),
        (KeyCode::Char('r'), Some(Restart)),
        (KeyCode::Char('q'), Some(Quit)),
        (KeyCode::Char('k'), None),
        (KeyCode::F(1), None),
    ];
    for (code, want) in cases {
        assert_eq!(key_to_command(press(code)), want, "{code:?}");
    }
}

#[test]
fn ctrl_c_quits_and_release_is_ignored() {
    let ctrl_c =
        KeyEvent::new(KeyCode::Char('c'), KeyModifiers::CONTROL);
    assert_eq!(key_to_command(ctrl_c), Some(Command::Quit));
    let mut up = press(KeyCode::Left);
    up.kind = KeyEventKind::Release;
    assert_eq!(
        key_to_command(up),
        None,
        "윈도는 뗄 때도 이벤트가 온다"
    );
}

#[test]
#[should_panic]
fn get_outside_the_row_panics() {
    // x 가 W 이상이면 다음 행의 칸을 돌려주지 말고 터져야 한다
    Screen::new().get(W, 0);
}
