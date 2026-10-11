#[derive(Debug)]
struct Address {
    city: String,
    zip: u32,
}

#[derive(Debug)]
struct User {
    name: String,
    address: Address, // 구조체 안의 구조체
}

fn main() {
    let u = User {
        name: String::from("kim"),
        address: Address {
            city: String::from("서울"),
            zip: 4524,
        },
    };
    println!("{u:?}");
    println!("{u:#?}"); // 여러 줄로 펴서
    println!("{} {} {}", u.name, u.address.city, u.address.zip);
}
