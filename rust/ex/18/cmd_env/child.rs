use std::env;

fn main() {
    // 두 변수가 보이는지만 한 줄로 찍는다
    let token = env::var("APP_TOKEN").ok();
    let lang = env::var("APP_LANG").ok();
    println!("APP_TOKEN {token:?}  APP_LANG {lang:?}");
}
