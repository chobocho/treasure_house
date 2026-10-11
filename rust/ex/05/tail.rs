fn area(w: u32, h: u32) -> u32 {
    w * h // 세미콜론이 없다 — 이 식의 값이 함수의 값이다
}

fn describe(n: i32) -> &'static str {
    if n < 0 { "음수" } else { "0 이상" }
}

fn main() {
    println!("{} {}", area(3, 4), describe(-5));
}
