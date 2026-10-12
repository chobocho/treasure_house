use std::ffi::OsStr;
use std::path::Path;

fn main() {
    for text in ["notes/2026/memo.txt", "backup.tar.gz", "notes", ".."]
    {
        let p = Path::new(text);
        // parent 만 경로이고 나머지 셋은 OsStr 이다
        let parent: Option<&Path> = p.parent();
        let name: Option<&OsStr> = p.file_name();
        let stem: Option<&OsStr> = p.file_stem();
        let ext: Option<&OsStr> = p.extension();
        println!("{text}");
        println!("  parent    {parent:?}");
        println!("  file_name {name:?}");
        println!("  file_stem {stem:?}");
        println!("  extension {ext:?}");
    }
}
