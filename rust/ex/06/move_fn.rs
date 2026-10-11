fn print_len(s: String) {
    println!("{}글자", s.len());
}

fn main() {
    let s = String::from("hello");
    print_len(s);
    println!("{s}");
}
//@ expect: E0382
