fn main() {
    let same = |x| x;
    let a = same(5);
    let b = same("다섯");
    println!("{a} {b}");
}
//@ expect: E0308
