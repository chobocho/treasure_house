fn main() {
    let s = String::from("한글");
    // 한글 한 글자는 UTF-8 로 3바이트다
    println!("{}바이트", s.len());
    println!("[{}]", &s[0..3]);

    // 첫 글자의 한가운데에서 자른다
    println!("[{}]", &s[0..1]);
}
//@ exit: 101
