use std::fs::{self, File};
use std::io::{self, BufWriter, Write};

// 지금 파일에 들어 있는 바이트 수
fn size(path: &str) -> io::Result<usize> {
    Ok(fs::read(path)?.len())
}

fn main() -> io::Result<()> {
    // File 에 바로 쓰면 쓴 글이 곧바로 파일에 들어간다
    let mut file = File::create("direct.txt")?;
    writeln!(file, "첫 줄")?;
    println!("File      쓴 뒤:    {}", size("direct.txt")?);

    // BufWriter 는 받은 글을 버퍼에 모아 둔다
    let mut out = BufWriter::new(File::create("buffered.txt")?);
    writeln!(out, "첫 줄")?;
    println!("BufWriter 쓴 뒤:    {}", size("buffered.txt")?);
    out.flush()?;
    println!("BufWriter flush 뒤: {}", size("buffered.txt")?);
    Ok(())
}
