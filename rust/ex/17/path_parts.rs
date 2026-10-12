use std::path::Path;

fn main() {
    for text in ["notes/2026/memo.txt", "backup.tar.gz", "notes", ".."]
    {
        let p = Path::new(text);
        println!("{text}");
        println!("  parent    {:?}", p.parent());
        println!("  file_name {:?}", p.file_name());
        println!("  file_stem {:?}", p.file_stem());
        println!("  extension {:?}", p.extension());
    }
}
