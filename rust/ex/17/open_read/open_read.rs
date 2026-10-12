use std::fs::File;
use std::io::{self, Read};

fn main() -> io::Result<()> {
    // 여는 일과 읽는 일을 따로 한다
    let mut file = File::open("memo.txt")?;
    let mut text = String::new();
    // 끝까지 읽어 text 에 담고, 읽은 바이트 수를 돌려준다
    let n = file.read_to_string(&mut text)?;
    println!("{n} 바이트를 읽었다");
    // 읽는 자리가 이미 파일 끝에 있다
    let again = file.read_to_string(&mut text)?;
    println!("다시 읽으면 {again} 바이트");
    println!("text 는 {} 바이트", text.len());
    Ok(())
}
