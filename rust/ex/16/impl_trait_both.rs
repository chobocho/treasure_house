use std::fmt::Display;

// 인자 자리 — 부르는 쪽이 타입을 고른다
fn show(item: impl Display) -> String {
    format!("[{item}]")
}

// 반환 자리 — 함수가 고른 타입 하나를 감춘다
fn evens(limit: u32) -> impl Iterator<Item = u32> {
    (0..limit).filter(|n| n % 2 == 0)
}

fn main() {
    println!("{} {}", show(7), show("seven"));
    let v: Vec<u32> = evens(7).collect();
    println!("{v:?}");
}
