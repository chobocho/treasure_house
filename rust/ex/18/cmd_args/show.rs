use std::env;

fn main() {
    // 받은 인자를 번호와 함께 찍는다. 0번은 프로그램 자신이다
    for (n, arg) in env::args().enumerate().skip(1) {
        println!("  {n}: {arg:?}");
    }
}
