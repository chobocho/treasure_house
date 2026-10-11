struct User {
    name: String,
}

impl User {
    // impl Into<String> — &str 이든 String 이든 받는다.
    fn new(name: impl Into<String>) -> User {
        User { name: name.into() }
    }
}

fn main() {
    let a = User::new("kim");
    let b = User::new(String::from("lee"));
    println!("{} {}", a.name, b.name);
}
