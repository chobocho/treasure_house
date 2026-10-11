fn main() {
    let mut s = String::from("hello");
    let r = &s;
    s.push_str(", world");
    println!("r = {r}");
    println!("s = {s}");
}
//@ expect: E0502
