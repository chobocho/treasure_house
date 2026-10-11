use std::collections::BTreeMap;

fn main() {
    let mut scores = BTreeMap::new();
    scores.insert("park", 70);
    scores.insert("kim", 90);
    scores.insert("lee", 85);

    // BTreeMap 은 늘 키 순서로 돈다 — 정렬할 필요가 없다.
    for (name, score) in &scores {
        println!("{name}: {score}");
    }
    println!(
        "{:?} {:?}",
        scores.first_key_value(),
        scores.last_key_value()
    );
    println!("{:?}", scores.range("l".."z").collect::<Vec<_>>());
}
