use std::fs::{self, File, OpenOptions};
use std::io::{self, ErrorKind};

// 열어 보고, 됐는지와 오류의 종류만 돌려준다
fn try_open(opts: &OpenOptions, path: &str) -> Result<(), ErrorKind> {
    opts.open(path).map(|_| ()).map_err(|e| e.kind())
}

fn main() -> io::Result<()> {
    let mut append = OpenOptions::new();
    append.append(true);
    let mut append_create = OpenOptions::new();
    append_create.append(true).create(true);
    let mut new_only = OpenOptions::new();
    new_only.write(true).create_new(true);

    let cases = [
        ("append", append),
        ("append+create", append_create),
        ("create_new", new_only),
    ];
    for (name, opts) in &cases {
        let path = format!("{name}.txt");
        let missing = try_open(opts, &path); // 아직 없는 파일
        fs::write(&path, "old\n")?;
        let existing = try_open(opts, &path); // 이제 있는 파일
        println!("{name:<14} {missing:?} / {existing:?}");
    }
    // File::create_new 는 셋째 조건을 줄인 이름이다
    let r = File::create_new("append.txt");
    println!("{:?}", r.map(|_| ()).map_err(|e| e.kind()));
    Ok(())
}
