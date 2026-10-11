fn add_world(s: &mut String) {
    s.push_str(", world");
}

fn main() {
    let s = String::from("hello");
    add_world(&mut s);
    println!("{s}");
}
//@ expect: E0596
