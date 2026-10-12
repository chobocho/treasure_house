fn main() {
    let one: u8 = 1;
    // u8 은 8 비트 — 밀 수 있는 칸 수는 0 부터 7 까지다
    println!("{}", one << 8);
}
//@ expect: error
