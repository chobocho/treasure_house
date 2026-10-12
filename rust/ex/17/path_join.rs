use std::path::{Path, PathBuf};

fn main() {
    let base = Path::new("notes");
    // join 은 새 PathBuf 를 돌려준다 — base 는 그대로다
    let memo = base.join("memo.txt");
    let deep = base.join("2026").join("10").join("log.txt");
    println!("{}", base.display());
    println!("{}", memo.display());
    println!("{}", deep.display());
    // 앞쪽이 구분자로 끝나도 구분자가 겹치지 않는다
    println!("{}", Path::new("notes/").join("memo.txt").display());

    // push 와 pop 은 가진 경로를 그 자리에서 고친다
    let mut dir = PathBuf::from("out");
    dir.push("logs");
    println!("{}", dir.display());
    dir.pop();
    println!("{}", dir.display());
}
