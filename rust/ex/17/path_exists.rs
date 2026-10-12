use std::fs;
use std::io;
use std::path::Path;

fn main() -> io::Result<()> {
    fs::write("memo.txt", "hello\n")?;
    // "." 은 지금 디렉터리, none.txt 는 없는 이름이다
    for text in ["memo.txt", ".", "none.txt"] {
        let p = Path::new(text);
        println!(
            "{text:<9} exists {:<5} is_file {:<5} is_dir {}",
            p.exists(),
            p.is_file(),
            p.is_dir()
        );
    }
    Ok(())
}
