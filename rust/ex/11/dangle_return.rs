fn make() -> &String {
    let s = String::from("hello");
    &s
}

fn main() {
    println!("{}", make());
}
//@ expect: E0106
