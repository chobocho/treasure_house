use std::fs::File;
use std::io::{self, BufRead, BufReader};

fn main() -> io::Result<()> {
    let reader = BufReader::new(File::open("mixed.txt")?);
    // 줄마다 따로 검사한다 — 깨진 줄에 이르러서야 Err 가 나온다
    for line in reader.lines() {
        println!("{line:?}");
    }
    Ok(())
}
