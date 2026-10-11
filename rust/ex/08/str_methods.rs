fn main() {
    let s = "  Hello, Rust!  ";

    println!("[{}]", s.trim());
    println!("[{}] [{}]", s.trim_start(), s.trim_end());
    let t = s.trim();
    println!("{} {}", t.to_uppercase(), t.to_lowercase());
    println!("{} {}", t.contains("Rust"), t.starts_with("Hello"));
    println!("{:?} {:?}", t.find("Rust"), t.find("Go"));
    println!("{}", t.replace("Rust", "World"));
    println!("{} {}", t.is_empty(), "".is_empty());
}
