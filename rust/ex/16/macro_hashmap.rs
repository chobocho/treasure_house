use std::collections::BTreeMap;

// vec! 처럼 쓰는 나만의 map! 매크로.
macro_rules! map {
    ($($key:expr => $value:expr),* $(,)?) => {{
        let mut m = BTreeMap::new();
        $(m.insert($key, $value);)*
        m
    }};
}

fn main() {
    let ports = map! {
        "http" => 80,
        "https" => 443,
    };
    println!("{ports:?}");
}
