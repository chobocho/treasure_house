fn main() {
    let s = String::from("hello");
    let a = &s;
    let b = &s;
    let c = &s;
    // 읽기만 하는 참조 셋이 한꺼번에 살아 있다
    println!("{a} {b} {c}");
    // 그동안 주인도 읽을 수 있다
    println!("{s} {}", a.len() + b.len() + c.len());
}
