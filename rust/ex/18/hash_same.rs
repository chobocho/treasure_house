use std::collections::HashMap;
use std::hash::{DefaultHasher, Hash, Hasher};

#[derive(Debug, PartialEq, Eq, Hash)]
struct Seat {
    row: u8,
    col: u8,
}

// 값을 Hasher 에 넣고, 나온 수 하나를 받는다
fn hash_of<T: Hash>(value: &T) -> u64 {
    let mut hasher = DefaultHasher::new();
    value.hash(&mut hasher);
    hasher.finish()
}

fn main() {
    let a = Seat { row: 3, col: 7 };
    let b = Seat { row: 3, col: 7 };
    let c = Seat { row: 7, col: 3 };
    // 따로 만든 a 와 b — 값이 같고 해시도 같다
    println!("{} {}", a == b, hash_of(&a) == hash_of(&b));
    println!("{} {}", a == c, hash_of(&a) == hash_of(&c));

    // 그래서 따로 만든 값으로도 같은 항목을 찾는다
    let mut owner = HashMap::new();
    owner.insert(a, "kim");
    println!("{:?} {:?}", owner.get(&b), owner.get(&c));
}
