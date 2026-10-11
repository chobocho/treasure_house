fn main() {
    let a = Box::new(String::from("hello"));
    let b = a; // 주소만 옮겨 간다 — 힙의 글자는 그대로
    println!("{b}");
    println!("{a}");
}
//@ expect: E0382
