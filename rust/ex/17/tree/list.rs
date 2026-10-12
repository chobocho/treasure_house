use std::fs;
use std::io;
use std::path::PathBuf;

fn main() -> io::Result<()> {
    let mut paths: Vec<PathBuf> = Vec::new();
    // read_dir 은 항목을 하나씩 내는 반복자다 — 항목마다 Result 다
    for entry in fs::read_dir("notes")? {
        let entry = entry?;
        paths.push(entry.path());
    }
    // 나오는 순서는 정해져 있지 않다 — 찍기 전에 정렬한다
    paths.sort();
    for path in &paths {
        let kind = if path.is_dir() {
            "디렉터리"
        } else {
            "파일"
        };
        println!("{:<16}{kind}", path.display());
    }
    Ok(())
}
