use std::fs;
use std::io;
use std::path::{Path, PathBuf};

// fs 의 함수들처럼, 경로로 볼 수 있는 것이면 무엇이든 받는다
fn size(path: impl AsRef<Path>) -> io::Result<usize> {
    Ok(fs::read(path)?.len())
}

fn main() -> io::Result<()> {
    fs::write("memo.txt", "hello\n")?;
    let name = String::from("memo.txt");
    let buf = PathBuf::from("memo.txt");

    println!("&str     {}", size("memo.txt")?);
    println!("&String  {}", size(&name)?);
    println!("String   {}", size(name)?);
    println!("&Path    {}", size(Path::new("memo.txt"))?);
    println!("&PathBuf {}", size(&buf)?);
    println!("PathBuf  {}", size(buf)?);
    Ok(())
}
