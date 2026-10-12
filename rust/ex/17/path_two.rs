use std::path::{Path, PathBuf};

// 읽기만 할 경로는 &Path 로 받는다
fn show(path: &Path) {
    println!("{}", path.display());
}

fn main() {
    // Path 는 빌린 경로다 — 있는 글을 경로로 볼 뿐이다
    let borrowed: &Path = Path::new("notes/memo.txt");
    // PathBuf 는 가진 경로다 — 그래서 늘릴 수 있다
    let mut owned: PathBuf = PathBuf::from("notes");
    owned.push("2026");
    owned.push("plan.txt");

    show(borrowed);
    // &PathBuf 는 &Path 자리에 그대로 들어간다
    show(&owned);

    // 빌린 경로에서 가진 경로를 만든다
    let copy: PathBuf = borrowed.to_path_buf();
    println!("{}", copy == borrowed);
}
