fn main() {
    let small: [u8; 32] = Default::default();
    let big: [u8; 33] = Default::default();
    println!("{} {}", small.len(), big.len());
}
//@ expect: E0277
