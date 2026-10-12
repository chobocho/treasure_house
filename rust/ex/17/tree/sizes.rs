use std::fs;
use std::io;

fn main() -> io::Result<()> {
    let mut rows = Vec::new();
    for entry in fs::read_dir("notes")? {
        let path = entry?.path();
        // metadata 는 내용이 아니라 파일에 대한 정보를 준다
        let meta = fs::metadata(&path)?;
        if meta.is_file() {
            rows.push((path, meta.len()));
        }
    }
    rows.sort();
    let mut total = 0;
    for (path, len) in &rows {
        println!("{len:>3} {}", path.display());
        total += len;
    }
    println!("{total:>3} 합계");
    Ok(())
}
