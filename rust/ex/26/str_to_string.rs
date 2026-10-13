fn greet(name: &str) -> String {
    format!("{name} 님")
}

fn main() {
    println!("{}", greet("가람"));
}
