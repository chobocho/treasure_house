use std::collections::HashMap;

fn main() {
    let text = "the quick fox jumps over the lazy dog the end";

    let mut counts: HashMap<&str, u32> = HashMap::new();
    for word in text.split(' ') {
        *counts.entry(word).or_insert(0) += 1;
    }

    // 맵을 도는 순서는 정해져 있지 않다 — 찍기 전에 정렬한다.
    let mut pairs: Vec<(&str, u32)> = counts.into_iter().collect();
    pairs.sort_by(|a, b| b.1.cmp(&a.1).then(a.0.cmp(b.0)));
    for (word, n) in pairs.iter().take(3) {
        println!("{word}: {n}");
    }
}
