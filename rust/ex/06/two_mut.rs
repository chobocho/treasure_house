fn main() {
    let mut s = String::from("hello");
    let a = &mut s;
    let b = &mut s;
    a.push_str(", a");
    b.push_str(", b");
    println!("{s}");
}
//@ expect: E0499
