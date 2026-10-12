use std::any::type_name;
use std::str::FromStr;

// 글을 T 로 읽는다. 못 읽으면 어떤 타입으로 읽으려 했는지 알린다
fn read<T: FromStr>(text: &str) -> Option<T> {
    let value = text.parse::<T>().ok();
    if value.is_none() {
        println!("  {text:?} 는 {} 로 읽히지 않는다", type_name::<T>());
    }
    value
}

// T 가 무엇으로 정해졌는지와 그 크기를 글로 돌려준다
fn describe<T>() -> String {
    format!("{} — {} 바이트", type_name::<T>(), size_of::<T>())
}

fn main() {
    let a: Option<u8> = read("200");
    let b: Option<u8> = read("300");
    let c: Option<f64> = read("3.5");
    let d: Option<bool> = read("yes");
    println!("{a:?} {b:?} {c:?} {d:?}");

    println!("{}", describe::<u8>());
    println!("{}", describe::<(u8, u32)>());
    // 긴 타입은 경로까지 적혀 나온다
    println!("{}", describe::<Option<String>>());
    println!("{}", describe::<Vec<&str>>());
}
