fn greet(name: &str) {
    println!("안녕, {name}!");
}

fn main() {
    let owned = String::from("Ferris");
    let boxed = Box::new(String::from("Rust"));

    greet("리터럴"); // &str 그대로
    greet(&owned); // &String → &str
    greet(&boxed); // &Box<String> → &String → &str
}
