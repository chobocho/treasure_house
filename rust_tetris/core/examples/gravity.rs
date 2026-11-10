//! 레벨별 중력 표를 찍는다.   cargo run -p tetris-core --example gravity
use tetris_core::Game;

fn main() {
    println!("레벨  ms/칸  칸/초");
    for level in [1, 2, 3, 5, 8, 10, 13, 15, 18, 20] {
        let ms = Game::gravity_ms(level);
        println!("{level:>4} {ms:>6} {:>6.1}", 1000.0 / ms as f64);
    }
}
