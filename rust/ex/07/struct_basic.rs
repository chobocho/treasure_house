// 이름 붙은 필드를 묶은 새 타입.
struct User {
    name: String,
    age: u32,
    active: bool,
}

fn main() {
    let u = User {
        name: String::from("kim"),
        age: 31,
        active: true,
    };
    println!("{} {} {}", u.name, u.age, u.active);
}
