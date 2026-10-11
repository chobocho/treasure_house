fn main() {
    let owned = String::from("rust");
    let lit = "rust";

    // String 과 &str 은 바로 견줄 수 있다.
    println!("{} {}", owned == lit, lit == owned);
    println!("{}", "Rust".eq_ignore_ascii_case("rUST"));
    // 순서는 바이트 값 순서 — 대문자가 소문자보다 앞이다.
    println!("{} {}", "Zebra" < "apple", "가" < "나");
}
