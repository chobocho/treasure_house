fn main() {
    greet("Ferris");
    let n = add(2, 3);
    println!("2 + 3 = {n}");
}

// main 보다 아래에 있어도 된다 — 선언 순서는 상관없다.
fn greet(name: &str) {
    println!("안녕, {name}!");
}

fn add(a: i32, b: i32) -> i32 {
    a + b
}
