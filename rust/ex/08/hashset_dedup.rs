use std::collections::HashSet;

fn main() {
    let words = ["b", "a", "b", "c", "a"];

    // 처음 본 것만 남긴다 — 순서를 지키며 겹친 것을 지운다.
    let mut seen = HashSet::new();
    let mut unique = Vec::new();
    for w in words {
        // insert 가 true 면 처음 본 것이다.
        if seen.insert(w) {
            unique.push(w);
        }
    }
    println!("{unique:?}");
    println!("{}", seen.len());
}
