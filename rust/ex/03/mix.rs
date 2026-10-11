fn main() {
    let stock: i64 = 1000;
    let order: i32 = 3;
    // 둘 다 정수지만 타입이 다르다
    println!("{}", stock > order);
}
//@ expect: E0308
