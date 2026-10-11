fn main() {
    let a = String::new(); // 빈 문자열
    let b = String::from("안녕");
    let c = "안녕".to_string();
    let d = "안녕".to_owned();
    let e: String = "안녕".into();
    let f = format!("{b}, {}!", "Rust");

    println!("{a:?} {b} {c} {d} {e}");
    println!("{f}");
}
