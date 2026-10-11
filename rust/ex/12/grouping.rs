use std::collections::BTreeMap;

fn main() {
    let words = ["apple", "avocado", "banana", "blueberry", "cherry"];

    // 첫 글자로 묶는다.
    let mut groups: BTreeMap<char, Vec<&str>> = BTreeMap::new();
    for w in words {
        let first = w.chars().next().unwrap_or('?');
        groups.entry(first).or_default().push(w);
    }
    for (letter, list) in &groups {
        println!("{letter}: {list:?}");
    }
}
