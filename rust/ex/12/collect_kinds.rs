use std::collections::{BTreeMap, BTreeSet};

fn main() {
    let words = ["b", "a", "b", "c"];

    // collect 는 받는 쪽의 타입을 보고 무엇을 만들지 정한다.
    let list: Vec<&str> = words.iter().copied().collect();
    let set: BTreeSet<&str> = words.iter().copied().collect();
    let text: String = words.iter().copied().collect();
    let map: BTreeMap<&str, usize> =
        words.iter().map(|w| (*w, w.len())).collect();

    println!("{list:?}\n{set:?}\n{text}\n{map:?}");
}
