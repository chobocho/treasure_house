use std::fs;
use std::io;
use std::path::{Path, PathBuf};

// dir 아래의 파일을 찾아 files 에 담는다
fn walk(dir: &Path, files: &mut Vec<PathBuf>) -> io::Result<()> {
    for entry in fs::read_dir(dir)? {
        let path = entry?.path();
        if path.is_dir() {
            // 디렉터리면 그 안으로 다시 들어간다
            walk(&path, files)?;
        } else {
            files.push(path);
        }
    }
    Ok(())
}

// root 아래의 모든 파일을 정렬해서 돌려준다
fn find_files(root: &Path) -> io::Result<Vec<PathBuf>> {
    let mut files = Vec::new();
    walk(root, &mut files)?;
    files.sort();
    Ok(files)
}

fn main() -> io::Result<()> {
    let files = find_files(Path::new("notes"))?;
    for file in &files {
        println!("{}", file.display());
    }
    let txt = files
        .iter()
        .filter(|p| p.extension().is_some_and(|ext| ext == "txt"))
        .count();
    println!("파일 {}개, 그 가운데 txt {txt}개", files.len());
    Ok(())
}
