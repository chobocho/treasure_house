use std::io;

fn main() -> io::Result<()> {
    // 입력이 끝날 때까지 읽어 String 하나로 받는다
    let text = io::read_to_string(io::stdin())?;
    println!("{} 줄", text.lines().count());
    println!("{} 낱말", text.split_whitespace().count());
    println!("{} 글자", text.chars().count());
    println!("{} 바이트", text.len());
    Ok(())
}
//@ stdin: 가나 다\nabc\n
