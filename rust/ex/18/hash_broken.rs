use std::collections::HashMap;
use std::hash::{BuildHasherDefault, DefaultHasher, Hash, Hasher};

// 대소문자를 가리지 않고 같다고 보는 이름
#[derive(Debug, Hash)]
struct Name(String);

impl PartialEq for Name {
    fn eq(&self, other: &Self) -> bool {
        self.0.eq_ignore_ascii_case(&other.0)
    }
}

impl Eq for Name {}

fn hash_of(name: &Name) -> u64 {
    let mut hasher = DefaultHasher::new();
    name.hash(&mut hasher);
    hasher.finish()
}

// 화면이 늘 같도록, 씨앗이 고정된 해시를 쓰는 맵
type FixedMap<K, V> = HashMap<K, V, BuildHasherDefault<DefaultHasher>>;

fn main() {
    let name = |s: &str| Name(s.to_string());
    let (a, b) = (name("Kim"), name("KIM"));
    // == 로는 같은데 해시는 다르다
    println!("{} {}", a == b, hash_of(&a) == hash_of(&b));

    let mut visits: FixedMap<Name, u32> = FixedMap::default();
    for who in ["Kim", "KIM", "kim", "Kim"] {
        *visits.entry(name(who)).or_insert(0) += 1;
    }
    // 한 사람이 네 번 왔는데 항목이 여럿이다
    println!("{}", visits.len());
    println!("{:?}", visits.get(&name("Kim")));
    println!("{:?}", visits.get(&name("kIM")));
}
