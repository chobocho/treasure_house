use std::fs::File;
use std::io::{self, BufRead, BufReader};

fn main() -> io::Result<()> {
    let file = File::open("scores.txt")?;
    // BufReader 로 감싸면 줄 단위로 읽을 수 있다
    let reader = BufReader::new(file);
    for (i, line) in reader.lines().enumerate() {
        let line = line?;
        println!("{}: {line}", i + 1);
    }
    Ok(())
}
