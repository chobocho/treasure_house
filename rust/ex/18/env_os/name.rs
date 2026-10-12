use std::env::{self, VarError};

fn main() {
    // var 의 Err 는 둘로 갈린다
    match env::var("APP_NAME") {
        Ok(name) => println!("var: {name}"),
        Err(VarError::NotPresent) => println!("var: 없다"),
        Err(VarError::NotUnicode(raw)) => {
            println!("var: 글이 아니다 {raw:?}")
        }
    }

    // var_os 는 검사하지 않고 OsString 으로 준다
    match env::var_os("APP_NAME") {
        Some(raw) => println!("var_os: {} 바이트", raw.len()),
        None => println!("var_os: 없다"),
    }
}
