fn main() {
    let n: i32 = "42".parse().unwrap();
    let x: f64 = "3.5".parse().unwrap();
    let b: bool = "true".parse().unwrap();
    let c: char = "가".parse().unwrap();
    println!("{} {} {} {}", n + 1, x * 2.0, !b, c);

    // 거꾸로 — 무엇이든 문자열로.
    let s = 42.to_string() + &3.5.to_string() + &true.to_string();
    println!("{s}");
}
