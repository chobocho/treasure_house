fn read_name() -> String {
    String::from("  가람  ")
}

fn main() {
    let name = read_name().trim();
    println!("[{name}]");
}
//@ expect: E0716
