fn main() {
    let name = String::from("가람");
    let seat = match name {
        "가람" => 1,
        _ => 0,
    };
    println!("{seat}");
}
//@ expect: E0308
