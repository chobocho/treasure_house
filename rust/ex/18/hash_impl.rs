use std::collections::HashMap;
use std::hash::{DefaultHasher, Hash, Hasher};

#[derive(Debug)]
struct Name(String);

impl PartialEq for Name {
    fn eq(&self, other: &Self) -> bool {
        self.0.eq_ignore_ascii_case(&other.0)
    }
}

impl Eq for Name {}

impl Hash for Name {
    // == 가 보는 것만 넣는다 — 소문자로 바꾼 글
    fn hash<H: Hasher>(&self, state: &mut H) {
        self.0.to_ascii_lowercase().hash(state);
    }
}

fn hash_of(name: &Name) -> u64 {
    let mut hasher = DefaultHasher::new();
    name.hash(&mut hasher);
    hasher.finish()
}

fn main() {
    let name = |s: &str| Name(s.to_string());
    let (a, b) = (name("Kim"), name("KIM"));
    println!("{} {}", a == b, hash_of(&a) == hash_of(&b));

    let mut visits: HashMap<Name, u32> = HashMap::new();
    for who in ["Kim", "KIM", "kim", "Kim", "Lee"] {
        *visits.entry(name(who)).or_insert(0) += 1;
    }
    println!("{}", visits.len());
    println!("{:?}", visits.get(&name("kIM")));
    // 맵에 남은 키는 처음 넣은 철자다
    let mut keys: Vec<&Name> = visits.keys().collect();
    keys.sort_by_key(|n| n.0.to_ascii_lowercase());
    println!("{keys:?}");
}
