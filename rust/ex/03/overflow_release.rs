use std::env;

fn main() {
    // 값을 실행할 때 받는다 — 컴파일러는 미리 알 수 없다
    let args: Vec<String> = env::args().collect();
    let level: u8 = args[1].parse().expect("수가 아니다");
    println!("지금: {level}");
    // u8 의 최댓값은 255 다
    let next = level + 10;
    println!("다음: {next}");
}
//@ args: 250
//@ flags: -O
