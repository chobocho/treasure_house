use std::fs::File;
use std::io::{self, Write};

fn main() -> io::Result<()> {
    // 쓰려고 연다 — 없는 파일이면 만든다
    let mut file = File::create("memo.txt")?;
    // 파일도 Write 다 — 1장의 writeln! 을 그대로 받는다
    writeln!(file, "장보기 {}가지", 2)?;
    for (i, item) in ["우유", "달걀"].iter().enumerate() {
        writeln!(file, "{}. {item}", i + 1)?;
    }
    println!("memo.txt 에 썼다");
    Ok(())
}
