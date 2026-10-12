use std::fs;
use std::io;

fn main() -> io::Result<()> {
    // 없는 파일이면 만들어서 쓴다
    fs::write("memo.txt", "우유\n달걀\n")?;
    println!("{:?}", fs::read_to_string("memo.txt")?);

    // 있는 파일이면 내용을 통째로 바꾼다 — 뒤에 붙지 않는다
    fs::write("memo.txt", "빵\n")?;
    println!("{:?}", fs::read_to_string("memo.txt")?);

    // 글이 아닌 바이트도 그대로 쓴다
    fs::write("raw.bin", [0u8, 159, 255])?;
    println!("{:?}", fs::read("raw.bin")?);
    Ok(())
}
