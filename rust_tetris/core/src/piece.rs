//! 일곱 가지 테트로미노, 회전 상태, SRS 월킥 표.
//!
//! 좌표계: x 는 오른쪽, y 는 **아래쪽**으로 늘어난다(화면 좌표와 같다).
//! 테트리스 위키의 SRS 표는 y 가 위로 늘어나므로 킥 값의 y 부호를
//! 뒤집어 쓴다 — `kicks()` 한 곳에서만 뒤집는다.

// ANCHOR: kind
/// 테트로미노 종류.
///
/// Java 의 `enum` 처럼 닫힌 집합이지만 값 하나가 1바이트이고,
/// `Copy` 라서 함수에 넘겨도 "이동"되지 않고 복사된다.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub enum Kind {
    I,
    O,
    T,
    S,
    Z,
    J,
    L,
}
// ANCHOR_END: kind

// ANCHOR: shapes
/// 스폰(0번 회전) 모양. 회전 상자 안의 (x, y) 네 칸.
const SHAPES: [[(i32, i32); 4]; 7] = [
    [(0, 1), (1, 1), (2, 1), (3, 1)], // I  ....
    [(0, 0), (1, 0), (0, 1), (1, 1)], // O  (2×2 상자)
    [(1, 0), (0, 1), (1, 1), (2, 1)], // T  .T. / TTT
    [(1, 0), (2, 0), (0, 1), (1, 1)], // S  .SS / SS.
    [(0, 0), (1, 0), (1, 1), (2, 1)], // Z  ZZ. / .ZZ
    [(0, 0), (0, 1), (1, 1), (2, 1)], // J  J.. / JJJ
    [(2, 0), (0, 1), (1, 1), (2, 1)], // L  ..L / LLL
];
// ANCHOR_END: shapes

// ANCHOR: kind_impl
impl Kind {
    pub const ALL: [Kind; 7] = [
        Kind::I,
        Kind::O,
        Kind::T,
        Kind::S,
        Kind::Z,
        Kind::J,
        Kind::L,
    ];

    /// 표(배열)를 찾아볼 때 쓰는 번호. `as usize` 는 선언 순서.
    pub fn index(self) -> usize {
        self as usize
    }

    /// 회전 상자 한 변의 길이.
    pub fn box_size(self) -> i32 {
        match self {
            Kind::I => 4,
            Kind::O => 2,
            _ => 3,
        }
    }

    pub fn spawn_cells(self) -> [(i32, i32); 4] {
        SHAPES[self.index()]
    }

    /// 시험용 판 그림(`"..TT.."`)을 읽을 때 쓴다.
    pub fn from_char(c: char) -> Option<Kind> {
        Kind::ALL.into_iter().find(|k| k.to_char() == c)
    }

    pub fn to_char(self) -> char {
        b"IOTSZJL"[self.index()] as char
    }
}
// ANCHOR_END: kind_impl

// ANCHOR: rot
/// 회전 상태. SRS 의 0 · R · 2 · L 에 차례로 대응한다.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Rot {
    R0,
    R1,
    R2,
    R3,
}

impl Rot {
    const ORDER: [Rot; 4] = [Rot::R0, Rot::R1, Rot::R2, Rot::R3];

    pub fn cw(self) -> Rot {
        Rot::ORDER[(self.index() + 1) % 4]
    }

    pub fn ccw(self) -> Rot {
        Rot::ORDER[(self.index() + 3) % 4]
    }

    pub fn index(self) -> usize {
        self as usize
    }
}
// ANCHOR_END: rot

// ANCHOR: piece
/// 판 위에 놓인 조각 하나. (x, y) 는 회전 상자의 왼쪽 위 모서리.
///
/// 필드 네 개가 전부 `Copy` 라서 구조체도 `Copy` 가 된다 — Go 의
/// 값 타입 struct 처럼 대입하면 통째로 복사된다.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Piece {
    pub kind: Kind,
    pub rot: Rot,
    pub x: i32,
    pub y: i32,
}
// ANCHOR_END: piece

// ANCHOR: piece_impl
impl Piece {
    /// 가이드라인대로 3·4열 가운데, 맨 윗줄에서 나온다.
    pub fn spawn(kind: Kind) -> Piece {
        let x = if kind == Kind::O { 4 } else { 3 };
        Piece {
            kind,
            rot: Rot::R0,
            x,
            y: 0,
        }
    }

    /// 판 좌표로 바꾼 네 칸.
    ///
    /// 회전은 표를 따로 두지 않고 상자 안에서 계산한다.
    /// 시계 방향 90°: (x, y) → (n−1−y, x). SRS 의 상태와 정확히 같다.
    pub fn cells(&self) -> [(i32, i32); 4] {
        let n = self.kind.box_size();
        let mut out = self.kind.spawn_cells();
        for c in out.iter_mut() {
            for _ in 0..self.rot.index() {
                *c = (n - 1 - c.1, c.0);
            }
            *c = (c.0 + self.x, c.1 + self.y);
        }
        out
    }

    /// 옮긴 사본을 돌려준다. `self` 를 값으로 받으므로 원본은 그대로.
    pub fn moved(self, dx: i32, dy: i32) -> Piece {
        Piece {
            x: self.x + dx,
            y: self.y + dy,
            ..self
        }
    }
}
// ANCHOR_END: piece_impl

// ANCHOR: kicks
type Kicks = [[(i32, i32); 5]; 4];

// 테트리스 위키의 표 그대로(y 위로). 줄 번호 = 출발 상태 0·R·2·L.
const JLSTZ_CW: Kicks = [
    [(0, 0), (-1, 0), (-1, 1), (0, -2), (-1, -2)], // 0→R
    [(0, 0), (1, 0), (1, -1), (0, 2), (1, 2)],     // R→2
    [(0, 0), (1, 0), (1, 1), (0, -2), (1, -2)],    // 2→L
    [(0, 0), (-1, 0), (-1, -1), (0, 2), (-1, 2)],  // L→0
];
const JLSTZ_CCW: Kicks = [
    [(0, 0), (1, 0), (1, 1), (0, -2), (1, -2)], // 0→L
    [(0, 0), (1, 0), (1, -1), (0, 2), (1, 2)],  // R→0
    [(0, 0), (-1, 0), (-1, 1), (0, -2), (-1, -2)], // 2→R
    [(0, 0), (-1, 0), (-1, -1), (0, 2), (-1, 2)], // L→2
];
const I_CW: Kicks = [
    [(0, 0), (-2, 0), (1, 0), (-2, -1), (1, 2)], // 0→R
    [(0, 0), (-1, 0), (2, 0), (-1, 2), (2, -1)], // R→2
    [(0, 0), (2, 0), (-1, 0), (2, 1), (-1, -2)], // 2→L
    [(0, 0), (1, 0), (-2, 0), (1, -2), (-2, 1)], // L→0
];
const I_CCW: Kicks = [
    [(0, 0), (-1, 0), (2, 0), (-1, 2), (2, -1)], // 0→L
    [(0, 0), (2, 0), (-1, 0), (2, 1), (-1, -2)], // R→0
    [(0, 0), (1, 0), (-2, 0), (1, -2), (-2, 1)], // 2→R
    [(0, 0), (-2, 0), (1, 0), (-2, -1), (1, 2)], // L→2
];
// ANCHOR_END: kicks

// ANCHOR: kick_fn
/// `from` 상태에서 돌릴 때 차례로 시험할 다섯 가지 이동(y 아래로).
pub fn kicks(kind: Kind, from: Rot, cw: bool) -> [(i32, i32); 5] {
    let table = match (kind, cw) {
        (Kind::O, _) => return [(0, 0); 5],
        (Kind::I, true) => &I_CW,
        (Kind::I, false) => &I_CCW,
        (_, true) => &JLSTZ_CW,
        (_, false) => &JLSTZ_CCW,
    };
    table[from.index()].map(|(dx, dy)| (dx, -dy))
}
// ANCHOR_END: kick_fn
