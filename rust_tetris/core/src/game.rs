//! 한 판의 진행 — 입력, 중력, 고정 지연, 줄 지우기, 점수.
//!
//! 시계를 직접 읽지 않는다. 프런트엔드가 지난 시간(ms)을 `tick` 에
//! 넘겨 주므로, 시험은 `tick(1000)` 한 줄로 1초를 흘려보낼 수 있다.

use crate::bag::Bag;
use crate::board::Board;
use crate::piece::{Kind, Piece, kicks};

pub const LOCK_DELAY_MS: u32 = 500;
pub const MAX_LOCK_RESETS: u32 = 15;
pub const PREVIEW: usize = 5;

/// 줄 수별 기본 점수(× 레벨). 0줄·1줄·2줄·3줄·4줄(테트리스).
const LINE_SCORE: [u32; 5] = [0, 100, 300, 500, 800];

// ANCHOR: action
/// 플레이어가 할 수 있는 일. 키 배치는 프런트엔드마다 다르지만
/// 코어는 이 여덟 가지만 안다.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Action {
    Left,
    Right,
    SoftDrop,
    HardDrop,
    RotateCw,
    RotateCcw,
    Hold,
    Pause,
}
// ANCHOR_END: action

// ANCHOR: game
#[derive(Clone, Debug)]
pub struct Game {
    board: Board,
    cur: Piece,
    bag: Bag,
    hold: Option<Kind>,
    hold_used: bool, // 이번 조각에서 홀드를 이미 썼나
    score: u32,
    lines: u32,
    level: u32,
    last_clear: u32, // 마지막 고정에서 지운 줄 수(효과용)
    over: bool,
    paused: bool,
    fall_ms: u32, // 중력 누적 시간
    lock_ms: u32, // 바닥에 닿은 뒤 누적 시간
    resets: u32,  // 이 조각이 고정 지연을 되돌린 횟수
}
// ANCHOR_END: game

impl Game {
    pub fn new(seed: u64) -> Game {
        Game::with_setup(Board::new(), &[], seed)
    }

    // ANCHOR: setup
    /// 판과 첫 조각들을 정해 놓고 시작한다(시험·튜토리얼용).
    pub fn with_setup(board: Board, queue: &[Kind], seed: u64) -> Game {
        let mut bag = Bag::with_prefix(seed, queue);
        let first = bag.draw();
        let mut g = Game {
            board,
            cur: Piece::spawn(first),
            bag,
            hold: None,
            hold_used: false,
            score: 0,
            lines: 0,
            level: 1,
            last_clear: 0,
            over: false,
            paused: false,
            fall_ms: 0,
            lock_ms: 0,
            resets: 0,
        };
        g.spawn(first);
        g
    }
    // ANCHOR_END: setup

    // ANCHOR: gravity
    /// 한 칸 떨어지는 데 걸리는 시간. 가이드라인 공식
    /// (0.8 − (레벨−1)×0.007)^(레벨−1) 초를 ms 로, 레벨 1~20 에서.
    pub fn gravity_ms(level: u32) -> u32 {
        let l = level.clamp(1, 20) - 1;
        let sec = (0.8 - l as f64 * 0.007).powi(l as i32);
        ((sec * 1000.0).round() as u32).max(1)
    }
    // ANCHOR_END: gravity

    // ANCHOR: apply
    /// 입력 하나를 처리한다. 실제로 무언가 바뀌었으면 `true`.
    pub fn apply(&mut self, a: Action) -> bool {
        if self.over {
            return false;
        }
        if a == Action::Pause {
            self.paused = !self.paused;
            return true;
        }
        if self.paused {
            return false;
        }
        let ok = match a {
            Action::Left => self.try_move(-1, 0),
            Action::Right => self.try_move(1, 0),
            Action::SoftDrop => {
                let ok = self.try_move(0, 1);
                if ok {
                    self.score += 1;
                    self.fall_ms = 0;
                }
                ok
            }
            Action::HardDrop => {
                let dist = self.ghost().y - self.cur.y;
                self.score += 2 * dist as u32;
                self.cur = self.ghost();
                self.lock_piece();
                return true;
            }
            Action::RotateCw => self.rotate(true),
            Action::RotateCcw => self.rotate(false),
            Action::Hold => return self.swap_hold(),
            Action::Pause => unreachable!("위에서 처리했다"),
        };
        if ok && self.lock_ms > 0 && self.resets < MAX_LOCK_RESETS {
            // 바닥에서 움직이면 고정을 미뤄 준다 — 단, 무한히는 아니다
            self.lock_ms = 0;
            self.resets += 1;
        }
        ok
    }
    // ANCHOR_END: apply

    // ANCHOR: tick
    /// 시간을 흘려보낸다. 바닥에 닿아 있으면 고정 지연을, 아니면
    /// 중력을 센다. 큰 값이 와도 넘치지 않게 포화 덧셈을 쓴다.
    pub fn tick(&mut self, dt_ms: u32) {
        if self.over || self.paused {
            return;
        }
        if self.grounded() {
            self.lock_ms = self.lock_ms.saturating_add(dt_ms);
            if self.lock_ms >= LOCK_DELAY_MS {
                self.lock_piece();
            }
            return;
        }
        self.lock_ms = 0;
        self.fall_ms = self.fall_ms.saturating_add(dt_ms);
        let g = Game::gravity_ms(self.level);
        while self.fall_ms >= g {
            self.fall_ms -= g;
            if !self.try_move(0, 1) {
                // 바닥에 닿았다. 남은 시간은 버리고 다음 tick 부터
                // 고정 지연을 센다.
                self.fall_ms = 0;
                break;
            }
        }
    }
    // ANCHOR_END: tick

    // ANCHOR: helpers
    fn grounded(&self) -> bool {
        !self.board.fits(&self.cur.moved(0, 1))
    }

    fn try_move(&mut self, dx: i32, dy: i32) -> bool {
        let p = self.cur.moved(dx, dy);
        let ok = self.board.fits(&p);
        if ok {
            self.cur = p;
        }
        ok
    }

    /// SRS: 제자리 회전이 막히면 킥 표의 이동을 차례로 시험한다.
    fn rotate(&mut self, cw: bool) -> bool {
        let to = if cw {
            self.cur.rot.cw()
        } else {
            self.cur.rot.ccw()
        };
        for (dx, dy) in kicks(self.cur.kind, self.cur.rot, cw) {
            let p = Piece {
                rot: to,
                ..self.cur
            }
            .moved(dx, dy);
            if self.board.fits(&p) {
                self.cur = p;
                return true;
            }
        }
        false
    }
    // ANCHOR_END: helpers

    // ANCHOR: lock
    fn spawn(&mut self, kind: Kind) {
        self.cur = Piece::spawn(kind);
        self.fall_ms = 0;
        self.lock_ms = 0;
        self.resets = 0;
        if !self.board.fits(&self.cur) {
            self.over = true; // block out: 나올 자리가 막혔다
        }
    }

    fn lock_piece(&mut self) {
        let inside = self.board.lock(&self.cur);
        let n = self.board.clear_lines();
        self.last_clear = n;
        // 시험용 판은 처음부터 꽉 찬 줄을 여럿 가질 수 있다 → min(4)
        self.score += LINE_SCORE[n.min(4) as usize] * self.level;
        self.lines += n;
        self.level = self.lines / 10 + 1;
        self.hold_used = false;
        if !inside {
            self.over = true; // lock out: 판 위로 삐져나와 굳었다
            return;
        }
        let k = self.bag.draw();
        self.spawn(k);
    }

    fn swap_hold(&mut self) -> bool {
        if self.hold_used {
            return false;
        }
        // Option::replace — 새 값을 넣고 옛 값을 돌려받는다
        let next = match self.hold.replace(self.cur.kind) {
            Some(k) => k,
            None => self.bag.draw(),
        };
        self.spawn(next);
        self.hold_used = true;
        true
    }
    // ANCHOR_END: lock

    // ANCHOR: getters
    pub fn board(&self) -> &Board {
        &self.board
    }

    pub fn current(&self) -> Piece {
        self.cur
    }

    /// 하드 드롭하면 떨어질 자리(그림자).
    pub fn ghost(&self) -> Piece {
        let mut p = self.cur;
        while self.board.fits(&p.moved(0, 1)) {
            p = p.moved(0, 1);
        }
        p
    }

    pub fn next_kinds(&self) -> impl Iterator<Item = Kind> + '_ {
        self.bag.peek().take(PREVIEW)
    }

    pub fn hold(&self) -> Option<Kind> {
        self.hold
    }

    pub fn score(&self) -> u32 {
        self.score
    }

    pub fn lines(&self) -> u32 {
        self.lines
    }

    pub fn level(&self) -> u32 {
        self.level
    }

    pub fn last_clear(&self) -> u32 {
        self.last_clear
    }

    pub fn is_over(&self) -> bool {
        self.over
    }

    pub fn is_paused(&self) -> bool {
        self.paused
    }
    // ANCHOR_END: getters
}
