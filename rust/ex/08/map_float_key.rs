use std::collections::HashMap;

fn main() {
    let mut m = HashMap::new();
    m.insert(1.5, "한 개 반");
    println!("{}", m.len());
}
//@ expect: E0277
