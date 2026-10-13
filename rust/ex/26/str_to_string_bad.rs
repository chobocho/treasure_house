fn greet(name: String) -> String {
    format!("{name} 님")
}

fn main() {
    println!("{}", greet("가람"));
}
//@ expect: E0308
