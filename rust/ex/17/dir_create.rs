use std::fs;
use std::io;
use std::path::Path;

fn main() -> io::Result<()> {
    let dir = Path::new("data/2026/10");
    let log = dir.join("log.txt");

    // 디렉터리가 없으면 그 안에 파일을 쓰지 못한다
    println!(
        "write  {:?}",
        fs::write(&log, "ok\n").map_err(|e| e.kind())
    );
    // create_dir 은 한 단만 만든다 — 위쪽이 없으면 실패한다
    println!("one    {:?}", fs::create_dir(dir).map_err(|e| e.kind()));
    // create_dir_all 은 길에 있는 디렉터리를 전부 만든다
    println!(
        "all    {:?}",
        fs::create_dir_all(dir).map_err(|e| e.kind())
    );
    println!("is_dir {}", dir.is_dir());

    // 이미 있는 디렉터리에 한 번씩 더 부른다
    println!("one    {:?}", fs::create_dir(dir).map_err(|e| e.kind()));
    println!(
        "all    {:?}",
        fs::create_dir_all(dir).map_err(|e| e.kind())
    );

    fs::write(&log, "ok\n")?;
    println!("read   {:?}", fs::read_to_string(&log));
    Ok(())
}
