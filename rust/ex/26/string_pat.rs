fn main() {
    let name = String::from("가람");
    let seat = match name.as_str() {
        "가람" => 1,
        _ => 0,
    };
    println!("{seat}");
}
