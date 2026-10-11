fn main() {
    let short = String::from("hi");
    let long = "rust ".repeat(1000);
    println!("{}바이트, {}바이트", short.len(), long.len());

    // 머리의 크기는 타입이 정한다. 글자 수와 상관없다.
    println!("String 의 머리 {}바이트", size_of::<String>());

    // 그래서 5000바이트짜리를 옮겨도 복사되는 것은 머리뿐이다
    let moved = long;
    println!("{}바이트", moved.len());
}
