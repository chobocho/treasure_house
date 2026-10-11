fn main() {
    let a = Box::new(String::from("hello"));
    let b = a; // 이동 — 이제 주인은 b 다
    println!("{b}");
    println!("{a}");
}
//@ expect: E0382
