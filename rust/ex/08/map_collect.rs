use std::collections::HashMap;

fn main() {
    let names = ["kim", "lee", "park"];
    let scores = [90, 85, 70];

    // zip 이 둘을 앞에서부터 (이름, 점수) 로 짝짓고,
    // collect 가 그 짝들을 맵으로 모은다.
    let table: HashMap<&str, i32> =
        names.into_iter().zip(scores).collect();

    let mut keys = Vec::new();
    for name in table.keys() {
        keys.push(*name); // keys() 는 키의 참조를 준다
    }
    keys.sort(); // 도는 순서는 정해져 있지 않다 — 정렬해서 찍는다
    println!("{keys:?}");

    let mut total = 0;
    for score in table.values() {
        total += score;
    }
    println!("{total}");
}
