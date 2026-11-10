//! 10×20 판 — 굳은 칸만 담는다. 떨어지는 조각은 `Game` 이 따로 든다.

use crate::piece::{Kind, Piece};

pub const WIDTH: usize = 10;
pub const HEIGHT: usize = 20;

// ANCHOR: board
/// 한 줄. 빈 칸은 `None`, 굳은 칸은 어느 조각이었는지(색을 위해).
pub type Row = [Option<Kind>; WIDTH];

/// 고정 크기 2차원 배열. `Vec<Vec<_>>` 와 달리 힙 할당이 없고
/// 200칸이 한 덩어리로 붙어 있어 복사·비교가 싸다.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Board {
    rows: [Row; HEIGHT],
}
// ANCHOR_END: board

impl Default for Board {
    fn default() -> Self {
        Board::new()
    }
}

impl Board {
    pub fn new() -> Board {
        Board {
            rows: [[None; WIDTH]; HEIGHT],
        }
    }

    // ANCHOR: from_rows
    /// 판 그림으로 만든다. 줄들은 **바닥에 붙여** 놓는다.
    ///
    /// ```
    /// use tetris_core::{Board, Kind};
    /// let b = Board::from_rows(&["T.........", "IIII......"]);
    /// assert_eq!(b.get(0, 19), Some(Kind::I));
    /// ```
    ///
    /// 그림이 잘못되면 패닉한다 — 시험·예제 전용이라 `Result` 보다
    /// 바로 터지는 쪽이 원인을 찾기 쉽다.
    pub fn from_rows(text: &[&str]) -> Board {
        assert!(text.len() <= HEIGHT, "판은 {HEIGHT}줄까지");
        let mut b = Board::new();
        let top = HEIGHT - text.len();
        for (i, line) in text.iter().enumerate() {
            let n = line.chars().count();
            assert_eq!(n, WIDTH, "줄마다 {WIDTH}칸: {line:?}");
            for (x, c) in line.chars().enumerate() {
                let cell =
                    match c {
                        '.' => None,
                        _ => Some(Kind::from_char(c).unwrap_or_else(
                            || panic!("모르는 칸 {c:?}"),
                        )),
                    };
                b.rows[top + i][x] = cell;
            }
        }
        b
    }
    // ANCHOR_END: from_rows

    pub fn to_rows(&self) -> Vec<String> {
        self.rows
            .iter()
            .map(|row| {
                row.iter()
                    .map(|c| c.map_or('.', Kind::to_char))
                    .collect()
            })
            .collect()
    }

    pub fn rows(&self) -> &[Row; HEIGHT] {
        &self.rows
    }

    // ANCHOR: query
    /// 굳은 칸. 판 밖이면 `None`.
    pub fn get(&self, x: i32, y: i32) -> Option<Kind> {
        let (x, y) =
            (usize::try_from(x).ok()?, usize::try_from(y).ok()?);
        *self.rows.get(y)?.get(x)?
    }

    /// 조각이 들어갈 수 있는 칸인가. 벽·바닥은 막혀 있고,
    /// 판 위쪽(y < 0)은 비어 있다 — 회전 킥이 위로 밀어 올릴 수 있다.
    pub fn is_free(&self, x: i32, y: i32) -> bool {
        let inside_x = (0..WIDTH as i32).contains(&x);
        inside_x
            && (y < 0
                || (y < HEIGHT as i32 && self.get(x, y).is_none()))
    }

    pub fn fits(&self, p: &Piece) -> bool {
        p.cells().iter().all(|&(x, y)| self.is_free(x, y))
    }
    // ANCHOR_END: query

    // ANCHOR: lock
    /// 조각을 판에 굳힌다. 네 칸이 모두 판 안에 들어왔으면 `true`,
    /// 하나라도 위로 삐져나왔으면 `false`(lock out — 게임 오버).
    pub fn lock(&mut self, p: &Piece) -> bool {
        let mut inside = true;
        for (x, y) in p.cells() {
            if y < 0 {
                inside = false;
            } else {
                self.rows[y as usize][x as usize] = Some(p.kind);
            }
        }
        inside
    }

    /// 꽉 찬 줄을 지우고 위를 내려 채운 뒤, 지운 줄 수를 돌려준다.
    ///
    /// 아래에서 위로 한 번 훑으며 "남길 줄"을 `write` 위치로 복사한다.
    /// O(WIDTH × HEIGHT) 시간, 추가 메모리 O(1).
    pub fn clear_lines(&mut self) -> u32 {
        let mut write = HEIGHT;
        for read in (0..HEIGHT).rev() {
            let full = self.rows[read].iter().all(Option::is_some);
            if !full {
                write -= 1;
                self.rows[write] = self.rows[read];
            }
        }
        // write 위쪽은 지운 줄 수만큼 빈 줄로
        for row in &mut self.rows[..write] {
            *row = [None; WIDTH];
        }
        write as u32
    }
    // ANCHOR_END: lock
}
