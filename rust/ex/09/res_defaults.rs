fn main() {
    let good: Result<i32, &str> = Ok(3);
    let bad: Result<i32, &str> = Err("고장");

    println!("{} {}", good.unwrap_or(0), bad.unwrap_or(0));
    // unwrap_or_else 의 클로저는 오류를 받는다(여기서는 안 쓴다).
    println!("{}", bad.unwrap_or_else(|_| -1));
    println!("{:?}", good.map(|n| n * 2));
    // map_err: 오류 쪽만 바꾼다.
    println!("{:?}", bad.map_err(|e| e.len()));
    println!("{} {}", good.is_ok(), bad.is_err());
}
