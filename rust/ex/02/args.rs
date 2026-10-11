use std::env;

fn main() {
    // 명령 줄 인자를 차례로 모은다 — 0번은 프로그램 자신이다
    let args: Vec<String> = env::args().collect();
    println!("{args:?}");
    // 인자는 모두 문자열로 온다 — 숫자로 쓰려면 parse
    let count: u32 = args[2].parse().expect("횟수는 숫자여야 한다");
    println!("{} 에게 {} 번 인사한다", args[1], count);
}
//@ args: Ferris 3
