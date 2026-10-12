use std::cmp::Reverse;
use std::collections::HashMap;

fn main() {
    // 짝의 배열에서 맵으로
    let mut stock = HashMap::from([("사과", 3), ("배", 1)]);
    // extend 는 짝을 내는 것을 받는다 — 벡터도, 다른 맵도
    let delivery = vec![("배", 7), ("감", 4)];
    stock.extend(delivery);
    let other = HashMap::from([("귤", 9)]);
    stock.extend(other);
    // 이미 있던 배는 새 값으로 바뀌었다
    println!("{} {:?}", stock.len(), stock.get("배"));

    // 맵에서 짝의 벡터로 — 순서는 정렬로 정한다
    let mut rows: Vec<(&str, u32)> = stock.into_iter().collect();
    rows.sort_by_key(|&(_, count)| Reverse(count));
    println!("{rows:?}");
    // 짝의 벡터에서 다시 맵으로
    let back: HashMap<&str, u32> = rows.into_iter().collect();
    println!("{} {:?}", back.len(), back.get("감"));
}
