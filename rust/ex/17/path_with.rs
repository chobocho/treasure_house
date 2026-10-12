use std::path::Path;

fn main() {
    let src = Path::new("notes/2026/memo.txt");
    // 한 조각만 바꾼 새 경로를 만든다 — src 는 그대로다
    println!("{}", src.with_extension("bak").display());
    println!("{}", src.with_extension("").display());
    println!("{}", src.with_file_name("todo.md").display());
    println!("{}", src.display());

    // components 는 경로를 조각으로 나눠 차례로 낸다
    let odd = Path::new("./notes/../notes//memo.txt");
    for part in odd.components() {
        println!("{part:?}");
    }
}
