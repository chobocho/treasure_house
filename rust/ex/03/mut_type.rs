fn main() {
    let mut spaces = "   ";
    println!("[{spaces}]");
    spaces = spaces.len();
    println!("{spaces}");
}
//@ expect: E0308
