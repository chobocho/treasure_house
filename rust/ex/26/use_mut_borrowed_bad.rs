fn main() {
    let mut count = 5;
    let r = &mut count;
    let double = count * 2;
    *r += 1;
    println!("{count} {double}");
}
//@ expect: E0503
