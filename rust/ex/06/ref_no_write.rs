fn add_world(s: &String) {
    s.push_str(", world");
}

fn main() {
    let s = String::from("hello");
    add_world(&s);
    println!("{s}");
}
//@ expect: E0596
