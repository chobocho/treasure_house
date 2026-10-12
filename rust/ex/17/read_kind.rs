use std::fs;
use std::io::{self, ErrorKind};

// 설정 파일이 없으면 기본값을 쓰고, 다른 오류는 올려 보낸다
fn load(path: &str) -> io::Result<String> {
    match fs::read_to_string(path) {
        Ok(text) => Ok(text),
        Err(e) if e.kind() == ErrorKind::NotFound => {
            Ok(String::from("port=8080"))
        }
        Err(e) => Err(e),
    }
}

fn main() {
    println!("{:?}", load("none.conf"));
    // "." 은 지금 디렉터리다 — 파일이 아니라서 읽지 못한다
    println!("{:?}", load("."));
}
