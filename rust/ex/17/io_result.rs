use std::fs;
use std::io;

// 반환 타입을 별명으로 적었다
fn short(path: &str) -> io::Result<usize> {
    Ok(fs::read_to_string(path)?.len())
}

// 같은 타입을 풀어서 적었다
fn long(path: &str) -> Result<usize, io::Error> {
    Ok(fs::read_to_string(path)?.len())
}

fn main() {
    // 서로의 타입 표기에 그대로 담긴다 — 같은 타입이다
    let a: Result<usize, io::Error> = short("none.txt");
    let b: io::Result<usize> = long("none.txt");
    println!("{a:?}");
    println!("{b:?}");
}
