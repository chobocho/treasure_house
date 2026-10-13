use std::fs::{self, File};
use std::io::{self, BufRead};

fn main() -> io::Result<()> {
    let text = "- 빨래\n장보기\n- 설거지\n청소\n분리수거\n";
    fs::write("chores.txt", text)?;

    // "- " 로 시작하는 줄은 끝낸 일이다.
    let file = File::open("chores.txt")?;
    let mut left = 0;
    for line in file.lines() {
        let line: String = line?;
        match line.strip_prefix("- ") {
            Some(done) => println!("끝냄 {done}"),
            None => {
                println!("남음 {line}");
                left += 1;
            }
        }
    }
    println!("남은 일 {left}개");
    Ok(())
}
//@ expect: E0599
