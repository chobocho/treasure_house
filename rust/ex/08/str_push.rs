fn main() {
    let mut s = String::from("Rust");
    s.push(' '); // 글자 하나
    s.push_str("언어"); // 문자열
    s += "!"; // += 도 된다
    println!("{s}");

    s.insert(0, '[');
    s.insert_str(1, "공부] ");
    println!("{s}");
}
