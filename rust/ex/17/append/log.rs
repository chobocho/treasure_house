use std::env;
use std::fs::OpenOptions;
use std::io::{self, Write};

fn main() -> io::Result<()> {
    let msg = env::args().nth(1).unwrap_or_default();
    // 없으면 만들고(create), 있으면 끝에 붙인다(append)
    let mut log = OpenOptions::new()
        .create(true)
        .append(true)
        .open("log.txt")?;
    writeln!(log, "{msg}")?;
    Ok(())
}
