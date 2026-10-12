use std::fs;
use std::io::ErrorKind;
use std::process::Command;

// 돌려 보고, 어떻게 됐는지를 한 줄로 알린다
fn run(program: &str, args: &[&str]) -> String {
    match Command::new(program).args(args).output() {
        Ok(out) if out.status.success() => String::from("성공"),
        Ok(out) => format!("실패로 끝났다 {:?}", out.status.code()),
        Err(e) if e.kind() == ErrorKind::NotFound => {
            String::from("돌리지 못했다 — 그런 프로그램이 없다")
        }
        Err(e) => format!("돌리지 못했다 — {:?}", e.kind()),
    }
}

fn main() {
    println!("echo    {}", run("echo", &["안녕"]));
    println!("sh      {}", run("sh", &["-c", "exit 3"]));
    println!("no-tool {}", run("no-such-tool", &[]));

    // 실행 파일이 아닌 파일을 돌리려 한다
    fs::write("memo.txt", "메모\n").expect("쓰지 못했다");
    println!("memo    {}", run("./memo.txt", &[]));
}
