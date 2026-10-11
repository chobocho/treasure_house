fn main() {
    let mut s = String::from("hello");
    let r = &s;
    println!("r = {r}");
    s.push_str(", world");
    println!("s = {s}");
}
