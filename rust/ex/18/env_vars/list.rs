use std::env;

fn main() {
    // 환경 변수 전체에서 APP_ 로 시작하는 것만 고른다
    let mut mine: Vec<(String, String)> = env::vars()
        .filter(|(key, _)| key.starts_with("APP_"))
        .collect();
    // 정렬해 두고 찍는다
    mine.sort();
    for (key, value) in &mine {
        println!("{key} = {value:?}");
    }
    println!("{} 개", mine.len());

    // 고르지 않은 변수도 있다. 그것들은 찍지 않는다
    println!("더 있다: {}", env::vars().count() > mine.len());
}
