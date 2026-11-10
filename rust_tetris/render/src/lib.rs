//! 게임 상태 → 0RGB 픽셀 버퍼(`u32` 한 개 = 한 픽셀, 0x00RRGGBB).
//!
//! minifb 창은 이 버퍼를 그대로 받고, WASM 은 `write_rgba` 로
//! 바이트 순서만 바꿔 캔버스에 넘긴다. 그리는 코드는 한 벌이다.

use tetris_core::{Game, HEIGHT, Kind, WIDTH};

pub mod font;

// ANCHOR: colors
pub const BG: u32 = 0x0010_131A;
pub const BOARD_BG: u32 = 0x001B_2030;
pub const GRID: u32 = 0x0023_2A3D;
pub const OVERLAY: u32 = 0x000B_0D14;
pub const TEXT: u32 = 0x00E8_ECF4;
pub const LABEL: u32 = 0x008A_94AD;

pub fn color(kind: Kind) -> u32 {
    match kind {
        Kind::I => 0x0031_C7EF,
        Kind::O => 0x00F7_D308,
        Kind::T => 0x00AD_4D9C,
        Kind::S => 0x0042_B642,
        Kind::Z => 0x00EF_2029,
        Kind::J => 0x005A_65AD,
        Kind::L => 0x00EF_7921,
    }
}

/// 그림자: 조각 색 1 : 판 색 3 으로 섞는다.
pub fn ghost_color(kind: Kind) -> u32 {
    mix(color(kind), BOARD_BG, 1, 3)
}

/// 채널마다 (a×wa + b×wb) / (wa+wb).
fn mix(a: u32, b: u32, wa: u32, wb: u32) -> u32 {
    let ch = |s: u32| {
        let (x, y) = ((a >> s) & 0xFF, (b >> s) & 0xFF);
        ((x * wa + y * wb) / (wa + wb)) << s
    };
    ch(16) | ch(8) | ch(0)
}
// ANCHOR_END: colors

// ANCHOR: frame
/// 그림판. 크기는 칸 하나의 픽셀 수(`cell`)로 정해진다.
#[derive(Clone, Debug)]
pub struct Frame {
    pub cell: usize,
    pub w: usize,
    pub h: usize,
    pub px: Vec<u32>,
}

impl Frame {
    /// 여백 = 반 칸. 가로: 여백·판 10칸·여백·패널 5칸·여백.
    pub fn new(cell: usize) -> Frame {
        assert!(cell >= 8, "cell >= 8 이어야 글자가 보인다");
        let pad = cell / 2;
        let w = pad * 3 + (WIDTH + 5) * cell;
        let h = pad * 2 + HEIGHT * cell;
        Frame {
            cell,
            w,
            h,
            px: vec![BG; w * h],
        }
    }

    pub fn board_origin(&self) -> (usize, usize) {
        (self.cell / 2, self.cell / 2)
    }

    /// 판 칸 (x, y) 한가운데 픽셀의 버퍼 번호(시험용).
    pub fn cell_center(&self, x: usize, y: usize) -> usize {
        let (ox, oy) = self.board_origin();
        let c = self.cell;
        (oy + y * c + c / 2) * self.w + ox + x * c + c / 2
    }

    /// 캔버스 `ImageData` 는 바이트 R·G·B·A 순서다.
    pub fn write_rgba(&self, out: &mut [u8]) {
        assert_eq!(out.len(), self.px.len() * 4, "RGBA 버퍼 크기");
        // as_chunks_mut: &mut [u8] → &mut [[u8; 4]] (길이가 상수인 조각)
        let (quads, _) = out.as_chunks_mut::<4>();
        for (p, o) in self.px.iter().zip(quads) {
            *o = [(p >> 16) as u8, (p >> 8) as u8, *p as u8, 0xFF];
        }
    }

    /// 사각형 채우기. 버퍼 밖으로 나가는 부분은 잘라 낸다.
    fn rect(&mut self, x: usize, y: usize, w: usize, h: usize, c: u32) {
        let (x1, y1) = ((x + w).min(self.w), (y + h).min(self.h));
        for yy in y.min(y1)..y1 {
            self.px[yy * self.w + x.min(x1)..yy * self.w + x1].fill(c);
        }
    }
}
// ANCHOR_END: frame

// ANCHOR: block
/// 칸 하나. 1px 틈을 두고 채운 뒤 위·왼쪽은 밝게, 아래·오른쪽은
/// 어둡게 테를 둘러 입체감을 낸다. 가운데는 원래 색 그대로.
fn block(f: &mut Frame, x: usize, y: usize, size: usize, c: u32) {
    let s = size - 1;
    let e = (size / 8).max(1);
    f.rect(x + 1, y + 1, s - 1, s - 1, c);
    f.rect(x + 1, y + 1, s - 1, e, mix(c, 0xFF_FFFF, 3, 2));
    f.rect(x + 1, y + 1, e, s - 1, mix(c, 0xFF_FFFF, 3, 2));
    f.rect(x + 1, y + s - e, s - 1, e, mix(c, 0, 3, 2));
    f.rect(x + s - e, y + 1, e, s - 1, mix(c, 0, 3, 2));
}
// ANCHOR_END: block

// ANCHOR: text
fn text(
    f: &mut Frame,
    x: usize,
    y: usize,
    s: &str,
    scale: usize,
    c: u32,
) {
    for (i, ch) in s.chars().enumerate() {
        let Some(g) = font::glyph(ch) else { continue }; // 공백 등
        let gx = x + i * 6 * scale;
        for (row, bits) in g.iter().enumerate() {
            for col in 0..5 {
                if bits & (0b10000 >> col) != 0 {
                    let (px, py) = (gx + col * scale, y + row * scale);
                    f.rect(px, py, scale, scale, c);
                }
            }
        }
    }
}
// ANCHOR_END: text

/// 미리보기 한 칸(판보다 작은 칸)에 조각 모양을 그린다.
fn mini(f: &mut Frame, x: usize, y: usize, kind: Kind, size: usize) {
    for (cx, cy) in kind.spawn_cells() {
        let (cx, cy) = (cx as usize, cy as usize);
        block(f, x + cx * size, y + cy * size, size, color(kind));
    }
}

// ANCHOR: draw
/// 한 프레임을 처음부터 다시 그린다. 버퍼 하나를 덮어쓰므로
/// 할당은 `Frame::new` 때 한 번뿐이다(숫자 문자열 제외).
pub fn draw(game: &Game, f: &mut Frame) {
    let c = f.cell;
    let (ox, oy) = f.board_origin();
    f.px.fill(BG);

    // 판 바탕과 1px 격자
    f.rect(ox, oy, WIDTH * c, HEIGHT * c, GRID);
    for y in 0..HEIGHT {
        for x in 0..WIDTH {
            f.rect(
                ox + x * c + 1,
                oy + y * c + 1,
                c - 1,
                c - 1,
                BOARD_BG,
            );
        }
    }

    // 굳은 칸
    for (y, row) in game.board().rows().iter().enumerate() {
        for (x, cell) in row.iter().enumerate() {
            if let Some(k) = cell {
                block(f, ox + x * c, oy + y * c, c, color(*k));
            }
        }
    }

    // 그림자 → 조각 순서로 그려야 겹칠 때 조각이 위에 온다
    if !game.is_over() {
        let ghost = game.ghost();
        for (x, y) in ghost.cells() {
            if y >= 0 {
                let (px, py) =
                    (ox + x as usize * c, oy + y as usize * c);
                f.rect(
                    px + 1,
                    py + 1,
                    c - 1,
                    c - 1,
                    ghost_color(ghost.kind),
                );
            }
        }
        let cur = game.current();
        for (x, y) in cur.cells() {
            if y >= 0 {
                let (px, py) =
                    (ox + x as usize * c, oy + y as usize * c);
                block(f, px, py, c, color(cur.kind));
            }
        }
    }

    panel(game, f);

    if game.is_over() || game.is_paused() {
        let msg = if game.is_over() {
            "GAME OVER"
        } else {
            "PAUSED"
        };
        f.rect(ox, oy + 8 * c, WIDTH * c, 4 * c, OVERLAY);
        let scale = (c / 10).max(1);
        let tw = font::text_width(msg, scale);
        let tx = ox + (WIDTH * c).saturating_sub(tw) / 2;
        let ty = oy + 10 * c - 7 * scale / 2;
        text(f, tx, ty, msg, scale, TEXT);
    }
}
// ANCHOR_END: draw

// ANCHOR: panel
/// 오른쪽 패널: 다음 조각 3개, 홀드, 점수·줄·레벨.
fn panel(game: &Game, f: &mut Frame) {
    let c = f.cell;
    let pad = c / 2;
    let x = pad * 2 + WIDTH * c;
    let scale = (c / 12).max(1);
    let line = 7 * scale + pad / 2; // 글자 한 줄 높이 + 사이
    let ms = c * 3 / 5; // 미리보기 칸 크기
    let mut y = pad;

    text(f, x, y, "NEXT", scale, LABEL);
    y += line;
    for k in game.next_kinds().take(3) {
        mini(f, x, y, k, ms);
        y += ms * 2 + pad;
    }

    y += pad;
    text(f, x, y, "HOLD", scale, LABEL);
    y += line;
    if let Some(k) = game.hold() {
        mini(f, x, y, k, ms);
    }
    y += ms * 2 + pad * 2;

    let stats = [
        ("SCORE", game.score()),
        ("LINES", game.lines()),
        ("LEVEL", game.level()),
    ];
    for (label, value) in stats {
        text(f, x, y, label, scale, LABEL);
        y += line;
        text(f, x, y, &value.to_string(), scale, TEXT);
        y += line + pad;
    }
}
// ANCHOR_END: panel
