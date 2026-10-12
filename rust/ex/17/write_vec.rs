use std::io::{self, Write};

fn main() -> io::Result<()> {
    // Vec<u8> 도 쓸 수 있는 곳이다 — 쓴 바이트가 끝에 붙는다
    let mut buf: Vec<u8> = Vec::new();
    writeln!(buf, "합계: {}", 42)?;
    write!(buf, "[{:>4}]", 7)?;
    println!("{} 바이트", buf.len());
    println!("{buf:?}");
    println!("{:?}", String::from_utf8(buf));
    Ok(())
}
