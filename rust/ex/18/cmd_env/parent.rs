use std::env;
use std::io;
use std::process::Command;

// 자식을 돌려, 자식이 찍은 한 줄을 이름표와 함께 찍는다
fn show(label: &str, cmd: &mut Command) -> io::Result<()> {
    let out = cmd.output()?;
    let line = String::from_utf8(out.stdout).expect("UTF-8 이 아니다");
    print!("{label:10} {line}");
    Ok(())
}

fn main() -> io::Result<()> {
    // 아무것도 안 하면 부모의 환경을 물려받는다
    let mut plain = Command::new("./child");
    show("plain", &mut plain)?;

    // env — 이 자식에게만 변수를 더한다
    let mut added = Command::new("./child");
    added.env("APP_LANG", "ko");
    show("env", &mut added)?;

    // env_remove — 하나를 빼고 준다
    let mut removed = Command::new("./child");
    removed.env_remove("APP_TOKEN");
    show("env_remove", &mut removed)?;

    // env_clear — 다 비우고, 그 뒤에 준 것만 준다
    let mut bare = Command::new("./child");
    bare.env_clear().env("APP_LANG", "en");
    show("env_clear", &mut bare)?;

    // 부모 자신의 환경은 바뀌지 않았다
    println!("부모의 APP_LANG {:?}", env::var("APP_LANG").ok());
    Ok(())
}
