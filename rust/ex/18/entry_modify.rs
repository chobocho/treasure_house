use std::collections::HashMap;

fn main() {
    let results = [
        ("kim", 72),
        ("lee", 88),
        ("kim", 91),
        ("lee", 64),
        ("kim", 80),
    ];
    // 이름마다 (가장 낮은 점수, 가장 높은 점수)
    let mut range: HashMap<&str, (u32, u32)> = HashMap::new();
    for (name, score) in results {
        range
            .entry(name)
            // 있으면 고친다
            .and_modify(|(low, high)| {
                *low = (*low).min(score);
                *high = (*high).max(score);
            })
            // 없으면 첫 점수로 시작한다
            .or_insert((score, score));
    }
    let mut rows: Vec<_> = range.into_iter().collect();
    rows.sort();
    println!("{rows:?}");
}
