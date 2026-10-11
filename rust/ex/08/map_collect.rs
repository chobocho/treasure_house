use std::collections::HashMap;

fn main() {
    let names = ["kim", "lee", "park"];
    let scores = [90, 85, 70];

    // (키, 값) 짝의 반복자를 맵으로 모은다.
    let table: HashMap<&str, i32> =
        names.iter().copied().zip(scores).collect();

    let mut keys: Vec<&&str> = table.keys().collect();
    keys.sort();
    println!("{keys:?}");
    println!("{}", table.values().sum::<i32>());
    println!("{:?}", table.iter().max_by_key(|(_, s)| **s));
}
