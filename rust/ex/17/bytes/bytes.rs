use std::fs;
use std::io;

fn main() -> io::Result<()> {
    // 글로 풀지 않고 바이트 그대로 읽는다
    let bytes: Vec<u8> = fs::read("hello.txt")?;
    println!("{} 바이트", bytes.len());
    println!("{bytes:?}");
    // 같은 파일을 글로 읽어 글자를 센다
    let text = fs::read_to_string("hello.txt")?;
    println!("{} 글자", text.chars().count());
    Ok(())
}
