use std::fs::{self, File};
use std::io::{self, BufWriter, Write};

fn size(path: &str) -> io::Result<usize> {
    Ok(fs::read(path)?.len())
}

fn main() -> io::Result<()> {
    let mut out = BufWriter::new(File::create("a.txt")?);
    writeln!(out, "첫 줄")?;
    println!("쓴 뒤:   {}", size("a.txt")?);
    // flush 를 부르지 않고 정리한다
    drop(out);
    println!("정리 뒤: {}", size("a.txt")?);

    {
        let mut out = BufWriter::new(File::create("b.txt")?);
        writeln!(out, "첫 줄")?;
        writeln!(out, "둘째 줄")?;
    } // 여기서 out 이 스코프를 벗어난다
    println!("블록 뒤: {}", size("b.txt")?);
    Ok(())
}
