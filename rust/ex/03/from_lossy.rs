fn main() {
    let big: i64 = 5_000_000_000;
    // i32 에는 21억쯤까지만 들어간다
    let small = i32::from(big);
    println!("{small}");
}
//@ expect: E0277
