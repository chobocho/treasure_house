fn clean(raw: &str) -> String {
    let lower = raw.to_lowercase();
    lower.trim().to_string()
}

fn main() {
    println!("[{}]", clean("  RUST  "));
}
