use std::fs;

fn main() {
    // 글로 읽는다 — 전체가 올바른 UTF-8 이어야 한다
    match fs::read_to_string("mixed.txt") {
        Ok(text) => println!("{text}"),
        Err(e) => {
            println!("{e}");
            println!("{:?}", e.kind());
        }
    }
    // 바이트로 읽는다 — 무엇이 들어 있든 읽힌다
    let bytes = fs::read("mixed.txt").unwrap();
    println!("{} 바이트", bytes.len());
    println!("{:?}", std::str::from_utf8(&bytes));
}
