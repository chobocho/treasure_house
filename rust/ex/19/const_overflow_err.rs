const fn kib(n: u32) -> u32 {
    n * 1024
}

const SMALL: u32 = kib(4);
// 4_194_304 * 1024 는 u32 에 들어가지 않는다.
const BIG: u32 = kib(4_194_304);

fn main() {
    println!("{SMALL} {BIG}");
}
//@ expect: E0080
