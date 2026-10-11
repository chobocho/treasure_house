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

    // 받는 변수가 없으면 메서드 쪽에 적는다(터보피시).
    let kinds = words.iter().collect::<BTreeSet<_>>().len();
    println!("{kinds}");
}
