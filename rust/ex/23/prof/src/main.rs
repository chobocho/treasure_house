use std::env;

fn main() {
    // 값을 실행할 때 받는다 — 컴파일러는 미리 알 수 없다.
    let args: Vec<String> = env::args().collect();
    let level: u8 = args[1].parse().unwrap();
    println!("debug_assertions = {}", cfg!(debug_assertions));
    // 디버그용 검사가 켜진 빌드에서만 확인하는 assert.
    debug_assert!(level != 0, "0 은 받지 않는다");
    // u8 의 최댓값은 255 다.
    let next = level + 10;
    println!("다음: {next}");
}
