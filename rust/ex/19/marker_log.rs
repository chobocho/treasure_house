use std::fmt::Debug;

// 로그에 찍어도 되는 타입에만 붙이는 표시. 메서드는 없다.
trait Loggable: Debug {}

#[derive(Debug)]
struct UserName(String);

#[derive(Debug)]
struct Password(String);

// Password 에는 붙이지 않는다.
impl Loggable for UserName {}

// Debug 만 요구하면 무엇이든 찍힌다.
fn dump<T: Debug>(what: &str, value: &T) {
    println!("[dump] {what}: {value:?}");
}

fn log<T: Loggable>(what: &str, value: &T) {
    println!("[log] {what}: {value:?}");
}

fn main() {
    let name = UserName(String::from("kim"));
    let secret = Password(String::from("1234"));
    println!("{} {}", name.0, secret.0.len());
    dump("비밀번호", &secret);
    log("로그인", &name);
}
