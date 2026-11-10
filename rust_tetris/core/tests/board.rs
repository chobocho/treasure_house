// 판 — 충돌 판정, 고정, 줄 지우기 시험.
use tetris_core::{Board, HEIGHT, Kind, Piece, Rot, WIDTH};

#[test]
fn new_board_is_empty() {
    let b = Board::new();
    let rows = b.to_rows();
    assert_eq!(rows.len(), HEIGHT);
    assert!(rows.iter().all(|r| r == ".........."));
    assert_eq!(b, Board::default());
}

#[test]
fn from_rows_is_bottom_aligned() {
    let b = Board::from_rows(&["T.........", "IIII......"]);
    assert_eq!(b.get(0, 19), Some(Kind::I));
    assert_eq!(b.get(3, 19), Some(Kind::I));
    assert_eq!(b.get(4, 19), None);
    assert_eq!(b.get(0, 18), Some(Kind::T));
    let rows = b.to_rows();
    assert_eq!(rows[18], "T.........");
    assert_eq!(rows[19], "IIII......");
    assert_eq!(Board::from_rows(&[]), Board::new());
}

#[test]
#[should_panic(expected = "모르는 칸")]
fn from_rows_rejects_unknown_char() {
    Board::from_rows(&["....x....."]);
}

#[test]
#[should_panic(expected = "10칸")]
fn from_rows_rejects_wrong_width() {
    Board::from_rows(&["..........."]);
}

#[test]
#[should_panic(expected = "20줄")]
fn from_rows_rejects_too_many_rows() {
    let rows = vec![".........."; HEIGHT + 1];
    Board::from_rows(&rows);
}

#[test]
fn bounds_of_is_free_and_get() {
    let b = Board::new();
    assert!(b.is_free(0, 0));
    assert!(b.is_free(9, 19));
    assert!(!b.is_free(-1, 5), "왼쪽 벽");
    assert!(!b.is_free(WIDTH as i32, 5), "오른쪽 벽");
    assert!(!b.is_free(5, HEIGHT as i32), "바닥");
    assert!(b.is_free(5, -1), "판 위쪽은 비어 있다");
    assert!(!b.is_free(-1, -1), "위쪽이어도 벽은 벽");
    assert_eq!(b.get(-1, 0), None);
    assert_eq!(b.get(0, 99), None);
}

#[test]
fn fits_and_lock() {
    let mut b = Board::from_rows(&["....T....."]);
    let mut p = Piece::spawn(Kind::O); // x=4, 칸 (4..5, 0..1)
    assert!(b.fits(&p));
    p.y = 18; // (4,19) 에 T 가 있다
    assert!(!b.fits(&p));
    p.y = 17;
    assert!(b.fits(&p));
    assert!(b.lock(&p));
    assert_eq!(b.get(5, 18), Some(Kind::O));
}

#[test]
fn lock_above_the_field_reports_false() {
    let mut b = Board::new();
    let p = Piece {
        kind: Kind::I,
        rot: Rot::R1,
        x: 0,
        y: -2,
    };
    assert!(b.fits(&p));
    assert!(!b.lock(&p), "칸 일부가 y<0 이면 lock out");
    // 보이는 칸은 그래도 찍힌다
    assert_eq!(b.get(2, 0), Some(Kind::I));
    assert_eq!(b.get(2, 1), Some(Kind::I));
}

#[test]
fn clear_nothing() {
    let mut b = Board::from_rows(&["IIIIIIIII."]);
    let before = b.clone();
    assert_eq!(b.clear_lines(), 0);
    assert_eq!(b, before);
}

#[test]
fn clear_non_adjacent_rows_compacts() {
    let mut b = Board::from_rows(&[
        "J.........",
        "LLLLLLLLLL",
        "S.S.S.S.S.",
        "ZZZZZZZZZZ",
    ]);
    assert_eq!(b.clear_lines(), 2);
    let rows = b.to_rows();
    assert_eq!(rows[19], "S.S.S.S.S.");
    assert_eq!(rows[18], "J.........");
    assert_eq!(rows[17], "..........");
}

#[test]
fn clear_full_board() {
    let rows = vec!["OOOOOOOOOO"; HEIGHT];
    let mut b = Board::from_rows(&rows);
    assert_eq!(b.clear_lines(), HEIGHT as u32);
    assert_eq!(b, Board::new());
}
