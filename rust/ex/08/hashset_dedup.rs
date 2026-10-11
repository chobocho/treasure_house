use std::collections::HashSet;

fn main() {
    let words = ["b", "a", "b", "c", "a"];

    // 처음 본 것만 남긴다 — 순서를 지키며 겹친 것을 지운다.
    let mut seen = HashSet::new();
    let unique: Vec<&str> =
        words.iter().copied().filter(|w| seen.insert(*w)).collect();
    println!("{unique:?}");
    println!("{}", seen.len());
}
