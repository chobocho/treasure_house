fn main() {
    // const { } — 이 식은 컴파일할 때 계산된다.
    let table = [const { 1u32 << 10 }; 3];
    println!("{table:?}");

    let secs_per_day = const { 60 * 60 * 24 };
    println!("{secs_per_day}");
}
