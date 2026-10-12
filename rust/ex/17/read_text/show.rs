use std::fs;
use std::io;

fn main() -> io::Result<()> {
    // 파일 전체를 String 하나로 읽는다
    let text = fs::read_to_string("memo.txt")?;
    println!("{} 줄, {} 바이트", text.lines().count(), text.len());
    for (i, line) in text.lines().enumerate() {
        println!("{}: {line}", i + 1);
    }
    Ok(())
}
