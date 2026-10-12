use std::io::{self, Write};

fn main() -> io::Result<()> {
    let mut out = io::stdout();
    let mut err = io::stderr();
    // 첫 인자가 "어디에 쓸지" 다
    writeln!(out, "합계: {}", 40 + 2)?;
    writeln!(err, "경고: 빈 줄 {}개", 2)?;
    write!(out, "줄바꿈 없이 ")?;
    writeln!(out, "이어서")?;
    Ok(())
}
