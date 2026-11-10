// 픽셀 렌더러 시험 — 화면을 눈으로 보기 전에 칸 색으로 확인한다.
use tetris_core::{Action, Board, Game, Kind};
use tetris_render::font::{glyph, text_width};
use tetris_render::{
    BG, BOARD_BG, Frame, OVERLAY, color, draw, ghost_color,
};

fn game(rows: &[&str], queue: &[Kind]) -> Game {
    Game::with_setup(Board::from_rows(rows), queue, 1)
}

fn at(f: &Frame, x: usize, y: usize) -> u32 {
    f.px[f.cell_center(x, y)]
}

#[test]
fn frame_size_follows_cell() {
    let f = Frame::new(24);
    // 좌우 여백 3개(12px) + 판 10칸 + 옆 패널 5칸, 위아래 여백 2개 + 20칸
    assert_eq!((f.w, f.h), (12 * 3 + 15 * 24, 12 * 2 + 20 * 24));
    assert_eq!(f.px.len(), f.w * f.h);
    assert_eq!(f.board_origin(), (12, 12));
    assert!(f.px.iter().all(|&p| p == BG), "새 버퍼는 배경색");
}

#[test]
#[should_panic(expected = "cell >= 8")]
fn tiny_cell_is_rejected() {
    Frame::new(7);
}

#[test]
fn smallest_cell_still_draws() {
    let mut f = Frame::new(8);
    draw(&Game::new(3), &mut f);
    assert_eq!(f.px.len(), f.w * f.h);
}

#[test]
fn empty_board_piece_and_ghost() {
    let mut f = Frame::new(20);
    draw(&game(&[], &[Kind::T]), &mut f);
    assert_eq!(at(&f, 0, 10), BOARD_BG);
    assert_eq!(at(&f, 4, 0), color(Kind::T), "떨어지는 T 의 혹");
    assert_eq!(at(&f, 4, 18), ghost_color(Kind::T), "그림자");
    assert_eq!(at(&f, 3, 19), ghost_color(Kind::T));
    assert_ne!(ghost_color(Kind::T), color(Kind::T));
}

#[test]
fn locked_cells_keep_their_color() {
    let mut f = Frame::new(20);
    draw(&game(&["I........J"], &[Kind::O]), &mut f);
    assert_eq!(at(&f, 0, 19), color(Kind::I));
    assert_eq!(at(&f, 9, 19), color(Kind::J));
}

#[test]
fn every_kind_has_a_distinct_color() {
    let mut seen: Vec<u32> =
        Kind::ALL.iter().map(|&k| color(k)).collect();
    seen.sort();
    seen.dedup();
    assert_eq!(seen.len(), 7);
    assert!(!seen.contains(&BOARD_BG));
}

#[test]
fn redraw_is_idempotent_and_clears_old_piece() {
    let mut f = Frame::new(20);
    let mut g = game(&[], &[Kind::T]);
    draw(&g, &mut f);
    let first = f.px.clone();
    draw(&g, &mut f);
    assert_eq!(f.px, first, "같은 상태 → 같은 그림");
    g.apply(Action::Right);
    draw(&g, &mut f);
    assert_eq!(at(&f, 4, 0), BOARD_BG, "옛 자리는 지워진다");
    assert_eq!(at(&f, 5, 0), color(Kind::T));
}

#[test]
fn game_over_and_pause_put_a_band_on_the_board() {
    let mut rows = vec![".........."; 20];
    rows[1] = "...LLL....";
    let mut f = Frame::new(20);
    draw(&game(&rows, &[Kind::T]), &mut f);
    assert_eq!(at(&f, 0, 9), OVERLAY, "가운데 띠");
    assert_eq!(at(&f, 0, 2), BOARD_BG, "띠 밖은 그대로");

    let mut g = game(&[], &[Kind::T]);
    g.apply(Action::Pause);
    draw(&g, &mut f);
    assert_eq!(at(&f, 0, 9), OVERLAY);
}

#[test]
fn rgba_conversion_for_canvas() {
    let mut f = Frame::new(8);
    f.px[0] = 0x0011_2233;
    let mut out = vec![0u8; f.w * f.h * 4];
    f.write_rgba(&mut out);
    assert_eq!(&out[..4], &[0x11, 0x22, 0x33, 0xFF]);
}

#[test]
#[should_panic(expected = "RGBA 버퍼 크기")]
fn rgba_buffer_must_match() {
    let f = Frame::new(8);
    f.write_rgba(&mut [0u8; 4]);
}

#[test]
fn font_covers_the_labels_only() {
    for s in [
        "NEXT",
        "HOLD",
        "SCORE",
        "LINES",
        "LEVEL",
        "PAUSED",
        "GAME OVER",
    ] {
        for c in s.chars().filter(|&c| c != ' ') {
            assert!(glyph(c).is_some(), "{c} 없음");
        }
    }
    for c in '0'..='9' {
        assert!(glyph(c).is_some());
    }
    assert_eq!(glyph('?'), None);
    assert_eq!(glyph('a'), glyph('A'), "소문자는 대문자로");
    // 글자 폭 5 + 사이 1, 마지막 글자 뒤 사이는 없다
    assert_eq!(text_width("AB", 1), 11);
    assert_eq!(text_width("AB", 2), 22);
    assert_eq!(text_width("", 3), 0);
}
