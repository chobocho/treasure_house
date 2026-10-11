struct User {
    name: String,
    age: u32,
}

fn new_user(name: String, age: u32) -> User {
    // 변수 이름과 필드 이름이 같으면 한 번만 쓴다.
    User { name, age }
}

fn main() {
    let u = new_user(String::from("lee"), 25);
    println!("{} {}", u.name, u.age);
}
