fn main() {
    let good: Result<i32, String> = Ok(3);
    let bad: Result<i32, String> = Err(String::from("고장"));

    println!(
        "{} {}",
        good.clone().unwrap_or(0),
        bad.clone().unwrap_or(0)
    );
    println!("{:?}", good.clone().map(|n| n * 2));
    // map_err: 오류 쪽만 바꾼다.
    println!("{:?}", bad.clone().map_err(|e| e.len()));
    println!("{} {}", good.is_ok(), bad.is_err());
}
