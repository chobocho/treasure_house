use std::io;
use std::process::Command;

fn main() -> io::Result<()> {
    // output 은 자식의 두 출력 길을 따로 모아서 돌려준다
    let out = Command::new("./report").output()?;
    println!("code   {:?}", out.status.code());
    println!("stdout {:?}", out.stdout);
    println!("stderr {} 바이트", out.stderr.len());

    // 모은 것은 바이트다. 검사를 거쳐 글이 된다
    let text = String::from_utf8(out.stdout).expect("UTF-8 이 아니다");
    println!("{text:?}");
    let total: u32 = text.trim().parse().expect("수가 아니다");
    println!("{}", total + 1);

    // 알림도 부모의 손에 있다. 찍을지는 부모가 정한다
    let warn = String::from_utf8(out.stderr).expect("UTF-8 이 아니다");
    println!("자식의 알림: {}", warn.trim_end());
    Ok(())
}
