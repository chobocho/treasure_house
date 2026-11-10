// 내보내기 함수 시험 — 브라우저 대신 네이티브에서 같은 함수를 부른다.
// 시험마다 스레드가 따로라 thread_local 상태도 시험마다 새것이다.
use tetris_wasm::*;

const HARD_DROP: u32 = 3;
const PAUSE: u32 = 7;
const RESTART: u32 = 8;
const SCORE: u32 = 0;
const OVER: u32 = 3;
const PAUSED: u32 = 4;

#[test]
fn calls_before_init_are_harmless() {
    assert_eq!(tt_input(HARD_DROP), 0);
    tt_tick(100);
    assert!(tt_render().is_null());
    assert_eq!((tt_width(), tt_height()), (0, 0));
    assert_eq!(tt_stat(SCORE), 0);
}

#[test]
fn init_rejects_bad_cell_sizes() {
    assert_eq!(tt_init(1, 0, 7), 0, "8 미만");
    assert_eq!(tt_init(1, 0, 65), 0, "64 초과");
    assert_eq!(tt_width(), 0, "실패한 init 은 상태를 만들지 않는다");
    assert_eq!(tt_init(1, 0, 8), 1);
    assert_eq!(tt_init(1, 0, 64), 1);
}

#[test]
fn size_matches_the_frame() {
    assert_eq!(tt_init(42, 0, 20), 1);
    let f = tetris_render::Frame::new(20);
    assert_eq!((tt_width(), tt_height()), (f.w as u32, f.h as u32));
}

#[test]
fn render_returns_rgba_bytes() {
    tt_init(42, 0, 16);
    let (w, h) = (tt_width() as usize, tt_height() as usize);
    let p = tt_render();
    assert!(!p.is_null());
    // 안전: tt_render 가 돌려준 포인터는 w×h×4 바이트 버퍼의 시작이다
    let px = unsafe { std::slice::from_raw_parts(p, w * h * 4) };
    assert!(px.chunks(4).all(|c| c[3] == 0xFF), "알파는 전부 불투명");
    assert_eq!(tt_render(), p, "버퍼는 다시 할당하지 않는다");
}

#[test]
fn input_codes_drive_the_game() {
    tt_init(42, 0, 16);
    assert_eq!(tt_input(HARD_DROP), 1);
    assert!(tt_stat(SCORE) > 0);
    assert_eq!(tt_input(99), 0, "모르는 코드");
    assert_eq!(tt_input(PAUSE), 1);
    assert_eq!(tt_stat(PAUSED), 1);
    tt_input(PAUSE);
    assert_eq!(tt_stat(PAUSED), 0);
    assert_eq!(tt_stat(77), 0, "모르는 통계");
}

#[test]
fn seed_uses_both_halves() {
    // 상위 32비트만 다른 두 씨앗 → 다른 조각 순서 → 다른 그림
    tt_init(5, 0, 16);
    let a = render_bytes();
    tt_init(5, 1, 16);
    let b = render_bytes();
    assert_ne!(a, b, "hi 가 무시되면 그림이 같다");
    tt_init(5, 0, 16);
    assert_eq!(render_bytes(), a, "같은 씨앗 → 같은 그림");
}

fn render_bytes() -> Vec<u8> {
    let n = (tt_width() * tt_height() * 4) as usize;
    let p = tt_render();
    unsafe { std::slice::from_raw_parts(p, n) }.to_vec()
}

#[test]
fn restart_only_after_game_over() {
    tt_init(3, 0, 16);
    assert_eq!(tt_input(RESTART), 0, "진행 중에는 무시");
    let mut guard = 0;
    while tt_stat(OVER) == 0 && guard < 500 {
        tt_input(HARD_DROP);
        guard += 1;
    }
    assert_eq!(tt_stat(OVER), 1, "하드 드롭만 하면 언젠가 끝난다");
    assert_eq!(tt_input(RESTART), 1);
    assert_eq!((tt_stat(OVER), tt_stat(SCORE)), (0, 0));
}
