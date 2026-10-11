#[derive(Debug)]
enum Level {
    Low,
    Mid,
    High,
}

// 정수 → 열거형은 직접 쓴다. 맞는 것이 없을 수 있으니 Option.
fn level(n: u8) -> Option<Level> {
    match n {
        0 => Some(Level::Low),
        1 => Some(Level::Mid),
        2 => Some(Level::High),
        _ => None,
    }
}

fn main() {
    println!("{:?} {:?}", level(1), level(9));
}
