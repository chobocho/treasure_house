fn main() {
    let some: Option<u32> = Some(8080);
    let none: Option<u32> = None;

    println!("{} {}", some.unwrap_or(80), none.unwrap_or(80));
    // 기본값을 만드는 데 일이 들면 클로저로 미룬다.
    println!("{}", none.unwrap_or_else(|| 40 * 2 + 1));
    // 타입의 기본값(u32 는 0).
    println!("{}", none.unwrap_or_default());
}
