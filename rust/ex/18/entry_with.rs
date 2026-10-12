use std::collections::HashMap;

// 읽는 데 일이 드는 설정이라고 하자
fn load(name: &str) -> String {
    println!("  ({name} 설정을 읽는다)");
    format!("새로 읽은 {name} 설정")
}

fn main() {
    let mut cache: HashMap<&str, String> = HashMap::new();
    cache.insert("db", String::from("넣어 둔 db 설정"));

    // or_insert — 인자를 먼저 만든다. 있는 키인데도 load 가 돈다
    println!("{}", cache.entry("db").or_insert(load("db")));
    // or_insert_with — 키가 없을 때만 클로저를 부른다
    println!("{}", cache.entry("db").or_insert_with(|| load("db")));
    println!("{}", cache.entry("web").or_insert_with(|| load("web")));
    println!("{}", cache.entry("web").or_insert_with(|| load("web")));

    // or_default — 없으면 그 타입의 기본값을 넣는다
    let mut hits: HashMap<&str, u32> = HashMap::new();
    *hits.entry("db").or_default() += 1;
    *hits.entry("db").or_default() += 1;
    println!("{}", hits["db"]);
}
