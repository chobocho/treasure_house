use std::fs::File;
use std::io::{self, BufRead, BufReader, BufWriter, Write};

// 빈 줄과 # 으로 시작하는 줄은 빼고 옮긴다. 옮긴 줄 수를 돌려준다
fn copy_lines(
    input: impl BufRead,
    out: &mut impl Write,
) -> io::Result<usize> {
    let mut count = 0;
    for line in input.lines() {
        let line = line?;
        if line.is_empty() || line.starts_with('#') {
            continue;
        }
        // lines() 가 뗀 줄바꿈을 writeln! 이 다시 붙인다
        writeln!(out, "{line}")?;
        count += 1;
    }
    Ok(count)
}

fn main() -> io::Result<()> {
    let input = BufReader::new(File::open("app.conf")?);
    let mut out = BufWriter::new(File::create("clean.conf")?);
    let n = copy_lines(input, &mut out)?;
    out.flush()?;
    println!("{n} 줄을 옮겼다");
    Ok(())
}
