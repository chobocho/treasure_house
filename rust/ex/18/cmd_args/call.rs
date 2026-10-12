use std::io;
use std::process::Command;

fn main() -> io::Result<()> {
    let out = Command::new("./show")
        // 빈칸이 든 글도 인자 하나다
        .arg("새 메모.txt")
        // 여럿은 args 로 한 번에
        .args(["-n", "3"])
        // 별표도, 따옴표도 적은 그대로 간다
        .arg("*.rs")
        .arg("'따옴표'")
        .output()?;
    let text = String::from_utf8(out.stdout).expect("UTF-8 이 아니다");
    print!("{text}");
    Ok(())
}
