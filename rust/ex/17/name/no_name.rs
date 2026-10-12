use std::fs;
use std::io;

fn main() -> io::Result<()> {
    for path in ["a.txt", "b.txt"] {
        let text = fs::read_to_string(path)?;
        println!("{path}: {} 바이트", text.len());
    }
    Ok(())
}
