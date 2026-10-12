use std::fs::{self, File};
use std::io;

fn main() -> io::Result<()> {
    fs::write("memo.txt", "지우면 안 되는 글\n")?;
    println!("처음: {} 바이트", fs::read("memo.txt")?.len());

    // 읽으려던 파일을 create 로 열었다 — 한 글자도 쓰지 않았다
    let _file = File::create("memo.txt")?;
    println!("create 뒤: {} 바이트", fs::read("memo.txt")?.len());
    Ok(())
}
