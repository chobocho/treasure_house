use std::num::ParseIntError;

// 어느 원소까지 읽는지 보려고, 읽을 때마다 한 줄 찍는다.
fn read(s: &str) -> Result<i32, ParseIntError> {
    println!("  읽는다: {s}");
    s.parse::<i32>()
}

fn main() {
    let good = ["1", "2", "3"];
    let bad = ["1", "둘", "3", "넷"];

    // Result 들의 목록을 "목록의 Result" 로 모은다. 첫 오류에서 멈춘다.
    let a: Result<Vec<i32>, _> = good.iter().map(|s| read(s)).collect();
    println!("{a:?}");
    let b: Result<Vec<i32>, _> = bad.iter().map(|s| read(s)).collect();
    println!("{b:?}");
}
