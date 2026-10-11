fn main() {
    let mut n = 1;
    let r = &n;
    n = 2;
    println!("{r} {n}");
}
//@ expect: E0506
