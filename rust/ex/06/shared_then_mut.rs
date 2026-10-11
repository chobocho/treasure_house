fn main() {
    let mut s = String::from("hello");
    let r = &s;
    let w = &mut s;
    w.push_str(", world");
    println!("{r}");
}
//@ expect: E0502
