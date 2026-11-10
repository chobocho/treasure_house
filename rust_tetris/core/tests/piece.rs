// 조각 모양·회전·월킥 표 시험.
use tetris_core::piece::kicks;
use tetris_core::{Kind, Piece, Rot};

fn sorted(mut v: [(i32, i32); 4]) -> [(i32, i32); 4] {
    v.sort();
    v
}

fn at(kind: Kind, rot: Rot) -> Piece {
    Piece {
        kind,
        rot,
        x: 0,
        y: 0,
    }
}

#[test]
fn rot_cycles_both_ways() {
    let mut r = Rot::R0;
    for _ in 0..4 {
        r = r.cw();
    }
    assert_eq!(r, Rot::R0);
    assert_eq!(Rot::R0.ccw(), Rot::R3);
    assert_eq!(Rot::R3.cw(), Rot::R0);
    assert_eq!(Rot::R2.index(), 2);
}

#[test]
fn every_rotation_has_four_distinct_cells_in_box() {
    for k in Kind::ALL {
        let n = k.box_size();
        for r in [Rot::R0, Rot::R1, Rot::R2, Rot::R3] {
            let c = sorted(at(k, r).cells());
            for w in c.windows(2) {
                assert_ne!(w[0], w[1], "{k:?} {r:?} 겹침");
            }
            for (x, y) in c {
                assert!((0..n).contains(&x) && (0..n).contains(&y));
            }
        }
    }
}

#[test]
fn t_and_i_states_match_srs() {
    // T 의 R 상태: 세로 막대 + 오른쪽 혹
    assert_eq!(
        sorted(at(Kind::T, Rot::R1).cells()),
        sorted([(1, 0), (1, 1), (1, 2), (2, 1)])
    );
    // I 는 4×4 상자의 셋째 열(x=2)에 선다
    assert_eq!(
        sorted(at(Kind::I, Rot::R1).cells()),
        [(2, 0), (2, 1), (2, 2), (2, 3)]
    );
    // I 의 2 상태는 셋째 행(y=2)
    assert_eq!(
        sorted(at(Kind::I, Rot::R2).cells()),
        [(0, 2), (1, 2), (2, 2), (3, 2)]
    );
}

#[test]
fn o_looks_the_same_in_every_state() {
    let base = sorted(at(Kind::O, Rot::R0).cells());
    for r in [Rot::R1, Rot::R2, Rot::R3] {
        assert_eq!(sorted(at(Kind::O, r).cells()), base);
    }
}

#[test]
fn spawn_position_and_moved() {
    let t = Piece::spawn(Kind::T);
    assert_eq!((t.x, t.y, t.rot), (3, 0, Rot::R0));
    assert_eq!(Piece::spawn(Kind::O).x, 4);
    let m = t.moved(-2, 5);
    assert_eq!((m.x, m.y), (1, 5));
    // moved 는 원본을 바꾸지 않는다 (Copy 값)
    assert_eq!(t.x, 3);
    assert_eq!(
        sorted(t.cells()),
        sorted([(4, 0), (3, 1), (4, 1), (5, 1)])
    );
}

#[test]
fn kind_char_round_trip() {
    for k in Kind::ALL {
        assert_eq!(Kind::from_char(k.to_char()), Some(k));
        assert_eq!(Kind::ALL[k.index()], k);
    }
    assert_eq!(Kind::from_char('x'), None);
    assert_eq!(Kind::from_char('.'), None);
}

#[test]
fn kick_tables_start_with_no_offset() {
    for k in Kind::ALL {
        for r in [Rot::R0, Rot::R1, Rot::R2, Rot::R3] {
            assert_eq!(kicks(k, r, true)[0], (0, 0));
            assert_eq!(kicks(k, r, false)[0], (0, 0));
        }
    }
    assert_eq!(kicks(Kind::O, Rot::R0, true), [(0, 0); 5]);
}

#[test]
fn kick_values_are_srs_with_y_down() {
    // 위키 표(y 위로)의 0→R: (0,0)(-1,0)(-1,+1)(0,-2)(-1,-2)
    assert_eq!(
        kicks(Kind::T, Rot::R0, true),
        [(0, 0), (-1, 0), (-1, -1), (0, 2), (-1, 2)]
    );
    // I 0→R: (0,0)(-2,0)(+1,0)(-2,-1)(+1,+2)
    assert_eq!(
        kicks(Kind::I, Rot::R0, true),
        [(0, 0), (-2, 0), (1, 0), (-2, 1), (1, -2)]
    );
}

#[test]
fn reverse_rotation_kicks_are_negated() {
    // SRS 의 성질: A→B 킥 = −(B→A 킥)
    for k in [Kind::I, Kind::T, Kind::J] {
        for r in [Rot::R0, Rot::R1, Rot::R2, Rot::R3] {
            let fwd = kicks(k, r, true);
            let back = kicks(k, r.cw(), false);
            for i in 0..5 {
                assert_eq!(fwd[i], (-back[i].0, -back[i].1));
            }
        }
    }
}
