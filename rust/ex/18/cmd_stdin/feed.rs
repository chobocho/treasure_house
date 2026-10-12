use std::io::{self, Write};
use std::process::{Command, Stdio};

fn main() -> io::Result<()> {
    // 자식의 입력과 출력을 부모와 이은 채로 띄운다
    let mut child = Command::new("./sorter")
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .spawn()?;

    // 자식의 표준 입력에 쓴다. 블록이 끝나면 손잡이가 닫힌다
    {
        let mut stdin = child.stdin.take().expect("stdin 이 없다");
        writeln!(stdin, "pear")?;
        writeln!(stdin, "apple")?;
        writeln!(stdin, "fig")?;
    }

    // 자식이 끝나기를 기다리며 출력을 모은다
    let out = child.wait_with_output()?;
    println!("code {:?}", out.status.code());
    let text = String::from_utf8(out.stdout).expect("UTF-8 이 아니다");
    print!("{text}");
    Ok(())
}
