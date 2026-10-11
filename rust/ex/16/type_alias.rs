use std::collections::BTreeMap;

// 긴 타입에 이름을 붙인다. 새 타입이 아니라 별명이다.
type Scores = BTreeMap<String, Vec<u32>>;
type Result<T> = std::result::Result<T, String>;

fn best(scores: &Scores, name: &str) -> Result<u32> {
    let list = scores.get(name).ok_or(format!("{name} 없음"))?;
    list.iter()
        .copied()
        .max()
        .ok_or(format!("{name} 점수 없음"))
}

fn main() {
    let mut scores = Scores::new();
    scores.insert(String::from("kim"), vec![70, 95, 80]);
    println!("{:?} {:?}", best(&scores, "kim"), best(&scores, "lee"));
}
