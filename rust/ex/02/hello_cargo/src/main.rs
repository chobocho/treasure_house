fn main() {
    println!("안녕, cargo!");
    // 디버그 빌드에서만 true 가 되는 값 — 두 빌드를 구별해 본다
    println!("debug_assertions = {}", cfg!(debug_assertions));
}
