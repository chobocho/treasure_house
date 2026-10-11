use std::collections::HashMap;

fn main() {
    let text = "the quick fox jumps over the lazy dog the end";

    let mut counts: HashMap<&str, u32> = HashMap::new();
    for word in text.split(' ') {
        *counts.entry(word).or_insert(0) += 1;
    }

    // 맵을 도는 순서는 정해져 있지 않다 — 찍기 전에 정렬한다.
    let mut pairs: Vec<(&str, u32)> = counts.into_iter().collect();
    pairs.sort(); // 튜플은 앞의 것부터 견준다 — 낱말 순서가 된다
    for (word, n) in pairs {
        println!("{word}: {n}");
    }
}
