use std::fs::File;
use std::io::{self, BufWriter, Write};
use std::process;

fn main() -> io::Result<()> {
    let mut out = BufWriter::new(File::create("result.txt")?);
    writeln!(out, "합계: 42")?;
    println!("result.txt 에 썼다");
    // 정리를 거치지 않고 끝낸다
    process::exit(0);
}
