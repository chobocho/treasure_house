fn main() {
    let mut s = String::from("hello");
    let w = &mut s;
    let r = &s;
    w.push_str(", world");
    println!("{r}");
}
//@ expect: E0502
