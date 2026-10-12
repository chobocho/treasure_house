use std::fs;
use std::io;
use std::path::Path;

fn main() -> io::Result<()> {
    fs::create_dir_all("tmp/cache")?;
    fs::write("tmp/cache/a.bin", [1u8, 2, 3])?;
    fs::create_dir("empty")?;

    // remove_dir 은 빈 디렉터리만 지운다
    println!(
        "empty {:?}",
        fs::remove_dir("empty").map_err(|e| e.kind())
    );
    println!("tmp   {:?}", fs::remove_dir("tmp").map_err(|e| e.kind()));
    println!("tmp 가 남았는가: {}", Path::new("tmp").exists());

    // remove_dir_all 은 안에 든 것까지 전부 지운다
    fs::remove_dir_all("tmp")?;
    println!("tmp 가 남았는가: {}", Path::new("tmp").exists());
    Ok(())
}
