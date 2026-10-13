fn clean(raw: &str) -> &str {
    let lower = raw.to_lowercase();
    lower.trim()
}

fn main() {
    println!("[{}]", clean("  RUST  "));
}
//@ expect: E0515
