fn read_name() -> String {
    String::from("  가람  ")
}

fn main() {
    let raw = read_name();
    let name = raw.trim();
    println!("[{name}]");
}
