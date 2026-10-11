// 기본 인자가 없다. "안 줘도 되는 값" 은 Option 으로 받는다.
fn greet(name: &str, greeting: Option<&str>) {
    let g = greeting.unwrap_or("안녕");
    println!("{g}, {name}!");
}

fn main() {
    greet("Ferris", None);
    greet("Ferris", Some("반가워"));
}
