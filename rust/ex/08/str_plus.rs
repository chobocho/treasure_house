fn main() {
    let hello = String::from("안녕, ");
    let name = String::from("Ferris");

    // + 의 왼쪽은 String(가져간다), 오른쪽은 &str(빌린다).
    let greeting = hello + &name;
    println!("{greeting}");
    println!("{name}"); // 빌려준 쪽은 그대로
}
