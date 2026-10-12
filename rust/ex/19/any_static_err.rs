use std::any::Any;

fn is_text(value: &dyn Any) -> bool {
    value.is::<&str>()
}

fn main() {
    println!("{}", is_text(&"hi"));
    let owned = String::from("hi");
    // owned 를 잠깐 빌린 &str
    let borrowed: &str = &owned;
    println!("{}", is_text(&borrowed));
}
//@ expect: E0597
