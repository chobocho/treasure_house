fn main() {
    // 밑줄은 읽기 좋으라고 넣는다 — 값은 그대로다
    let million = 1_000_000;
    let hex = 0xff;
    let octal = 0o17;
    let binary = 0b1010_0001;
    println!("{million} {hex} {octal} {binary}");

    // 바이트 리터럴 — 글자 a 의 바이트 값, 타입은 u8
    let byte = b'a';
    // 접미사를 붙이면 리터럴의 타입이 정해진다
    let small = 42u8;
    let big = 5_000_000_000_i64;
    println!("{byte} {small} {big}");
}
