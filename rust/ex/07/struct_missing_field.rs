struct User {
    name: String,
    age: u32,
}

fn main() {
    let u = User {
        name: String::from("kim"),
    };
    println!("{} {}", u.name, u.age);
}
//@ expect: E0063
