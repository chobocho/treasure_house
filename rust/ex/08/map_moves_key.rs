use std::collections::HashMap;

fn main() {
    let key = String::from("색");
    let value = String::from("파랑");

    let mut prefs = HashMap::new();
    prefs.insert(key, value);
    println!("{key} {value}");
}
//@ expect: E0382
