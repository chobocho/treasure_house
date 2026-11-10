// 게임 진행 시험 — 점수, 줄, 레벨, 홀드, 중력, 고정 지연, 게임 오버.
use tetris_core::game::{LOCK_DELAY_MS, MAX_LOCK_RESETS};
use tetris_core::{Action, Board, Game, Kind, Rot};

/// 위에서부터 20줄을 다 적는 대신, 아래쪽 줄만 적고 나머지는 빈 줄.
fn game(rows: &[&str], queue: &[Kind]) -> Game {
    Game::with_setup(Board::from_rows(rows), queue, 1)
}

/// 바닥에 닿을 때까지 소프트 드롭.
fn to_floor(g: &mut Game) {
    while g.apply(Action::SoftDrop) {}
}

#[test]
fn fresh_game() {
    let g = Game::new(123);
    assert_eq!((g.score(), g.lines(), g.level()), (0, 0, 1));
    assert!(!g.is_over() && !g.is_paused());
    assert_eq!(g.hold(), None);
    assert_eq!(g.next_kinds().count(), 5);
    assert_eq!(g.current().y, 0);
}

#[test]
fn queue_controls_the_first_pieces() {
    let g = game(&[], &[Kind::S, Kind::Z, Kind::L]);
    assert_eq!(g.current().kind, Kind::S);
    let next: Vec<Kind> = g.next_kinds().take(2).collect();
    assert_eq!(next, [Kind::Z, Kind::L]);
}

#[test]
fn hard_drop_scores_two_per_row_and_locks() {
    let mut g = game(&[], &[Kind::T, Kind::O]);
    assert_eq!(g.ghost().y, 18);
    assert!(g.apply(Action::HardDrop));
    assert_eq!(g.score(), 36); // 18칸 × 2점
    let rows = g.board().to_rows();
    assert_eq!(rows[18], "....T.....");
    assert_eq!(rows[19], "...TTT....");
    assert_eq!(g.current().kind, Kind::O);
}

#[test]
fn soft_drop_scores_one_per_row() {
    let mut g = game(&[], &[Kind::T]);
    assert!(g.apply(Action::SoftDrop));
    assert!(g.apply(Action::SoftDrop));
    assert_eq!(g.score(), 2);
    assert_eq!(g.current().y, 2);
}

#[test]
fn single_line_clear() {
    let mut g = game(&["III....III"], &[Kind::I, Kind::T]);
    g.apply(Action::HardDrop);
    assert_eq!(g.lines(), 1);
    assert_eq!(g.last_clear(), 1);
    assert_eq!(g.score(), 36 + 100);
    assert_eq!(g.board(), &Board::new());
}

#[test]
fn tetris_with_rotation_and_moves() {
    let well = "IIIIIIIII.";
    let mut g = game(&[well, well, well, well], &[Kind::I, Kind::T]);
    assert!(g.apply(Action::RotateCw)); // 세로 I, x 열 = 5
    for _ in 0..4 {
        assert!(g.apply(Action::Right));
    }
    assert!(!g.apply(Action::Right), "벽");
    g.apply(Action::HardDrop);
    assert_eq!(g.lines(), 4);
    assert_eq!(g.score(), 16 * 2 + 800);
    assert_eq!(g.board(), &Board::new());
}

#[test]
fn level_rises_every_ten_lines() {
    let well = "IIIIIIIII.";
    let mut g =
        game(&[well; 12], &[Kind::I, Kind::I, Kind::I, Kind::T]);
    for _ in 0..3 {
        g.apply(Action::RotateCw);
        for _ in 0..4 {
            g.apply(Action::Right);
        }
        g.apply(Action::HardDrop);
    }
    assert_eq!(g.lines(), 12);
    assert_eq!(g.level(), 2);
    // 세 번 다 레벨 1 에서 지웠다. 9열이 바닥까지 비어 있어 매번 16칸 낙하
    assert_eq!(g.score(), 16 * 3 * 2 + 800 * 3);
}

#[test]
fn hold_once_per_piece() {
    let mut g = game(&[], &[Kind::T, Kind::S, Kind::Z]);
    assert!(g.apply(Action::Hold));
    assert_eq!(g.hold(), Some(Kind::T));
    assert_eq!(g.current().kind, Kind::S);
    assert!(!g.apply(Action::Hold), "같은 조각에서 두 번은 안 된다");
    g.apply(Action::HardDrop);
    assert_eq!(g.current().kind, Kind::Z);
    assert!(g.apply(Action::Hold));
    assert_eq!(g.hold(), Some(Kind::Z));
    assert_eq!(g.current().kind, Kind::T);
    assert_eq!(g.current().y, 0, "꺼낸 조각은 스폰 위치에서");
}

#[test]
fn gravity_follows_the_level_table() {
    assert_eq!(Game::gravity_ms(1), 1000);
    assert!(Game::gravity_ms(2) < 1000);
    assert!(Game::gravity_ms(20) >= 1, "0ms 가 되면 안 된다");
    assert_eq!(Game::gravity_ms(0), Game::gravity_ms(1));
    let mut g = game(&[], &[Kind::T]);
    g.tick(0);
    g.tick(999);
    assert_eq!(g.current().y, 0);
    g.tick(1);
    assert_eq!(g.current().y, 1);
}

#[test]
fn lock_delay_then_lock() {
    let mut g = game(&[], &[Kind::T, Kind::O]);
    to_floor(&mut g);
    g.tick(LOCK_DELAY_MS - 1);
    assert_eq!(g.current().kind, Kind::T);
    g.tick(1);
    assert_eq!(g.current().kind, Kind::O, "고정되고 다음 조각");
    assert_eq!(g.board().to_rows()[19], "...TTT....");
}

#[test]
fn moving_on_the_floor_resets_lock_delay() {
    let mut g = game(&[], &[Kind::T, Kind::O]);
    to_floor(&mut g);
    for i in 0..MAX_LOCK_RESETS {
        g.tick(LOCK_DELAY_MS - 100);
        let a = if i % 2 == 0 {
            Action::Left
        } else {
            Action::Right
        };
        assert!(g.apply(a));
        assert_eq!(g.current().kind, Kind::T);
    }
    // 초기화 횟수를 다 쓴 뒤의 이동은 타이머를 되돌리지 않는다
    g.tick(LOCK_DELAY_MS - 100);
    assert!(g.apply(Action::Left));
    g.tick(100);
    assert_eq!(g.current().kind, Kind::O);
}

#[test]
fn huge_tick_falls_but_locks_on_the_next() {
    let mut g = game(&[], &[Kind::T, Kind::O]);
    g.tick(1_000_000);
    assert_eq!(g.current().kind, Kind::T);
    assert_eq!(g.current().y, g.ghost().y);
    g.tick(u32::MAX);
    assert_eq!(g.current().kind, Kind::O);
}

#[test]
fn pause_freezes_everything() {
    let mut g = game(&[], &[Kind::T]);
    assert!(g.apply(Action::Pause));
    assert!(g.is_paused());
    g.tick(5000);
    assert_eq!(g.current().y, 0);
    assert!(!g.apply(Action::Left));
    assert!(g.apply(Action::Pause));
    assert!(!g.is_paused());
    assert!(g.apply(Action::Left));
}

#[test]
fn wall_kick_off_the_left_wall() {
    let mut g = game(&[], &[Kind::T]);
    g.apply(Action::RotateCw); // R: 칸이 상자 1~2열
    while g.apply(Action::Left) {}
    assert_eq!(g.current().x, -1);
    assert!(g.apply(Action::RotateCcw)); // R→0, 킥 (+1, 0)
    let p = g.current();
    assert_eq!((p.rot, p.x, p.y), (Rot::R0, 0, 0));
}

#[test]
fn i_kick_off_the_left_wall() {
    let mut g = game(&[], &[Kind::I]);
    g.apply(Action::RotateCw); // 상자 2열에 세로
    while g.apply(Action::Left) {}
    assert_eq!(g.current().x, -2);
    assert!(g.apply(Action::RotateCw)); // R→2, 킥 (+2, 0)
    let p = g.current();
    assert_eq!((p.rot, p.x, p.y), (Rot::R2, 0, 0));
}

#[test]
fn rotation_fails_when_every_kick_is_blocked() {
    let mut rows = vec![".........."; 20];
    rows[0] = "LLLLLLLLLL";
    rows[1] = "LLL....LLL";
    rows[2] = "LLLLLLLLLL";
    let mut g = game(&rows, &[Kind::I]);
    assert!(!g.is_over());
    let before = g.current();
    assert!(!g.apply(Action::RotateCw));
    assert!(!g.apply(Action::RotateCcw));
    assert_eq!(g.current(), before);
}

#[test]
fn block_out_when_spawn_is_covered() {
    let mut rows = vec![".........."; 20];
    rows[1] = "...LLL....";
    let mut g = game(&rows, &[Kind::T]);
    assert!(g.is_over());
    assert!(!g.apply(Action::Left));
    g.tick(10_000); // 끝난 판에서도 패닉 없이
    assert!(g.is_over());
}

#[test]
fn top_out_after_stacking() {
    let col = "....JJ....";
    let mut g = game(&[col; 18], &[Kind::O, Kind::T]);
    assert!(!g.is_over());
    g.apply(Action::HardDrop); // O 가 0~1행에 고정
    assert!(g.is_over(), "다음 T 가 나올 자리가 없다");
}

#[test]
fn game_is_deterministic_for_a_seed() {
    let play = |seed| {
        let mut g = Game::new(seed);
        for i in 0..200u32 {
            let a = match i % 5 {
                0 => Action::Left,
                1 => Action::RotateCw,
                2 => Action::Right,
                3 => Action::Right,
                _ => Action::HardDrop,
            };
            g.apply(a);
            g.tick(16);
        }
        (g.score(), g.board().to_rows())
    };
    assert_eq!(play(9), play(9));
}
