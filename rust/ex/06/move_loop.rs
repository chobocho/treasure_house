fn consume(s: String) {
    println!("{s}");
}

fn main() {
    let s = String::from("hello");
    for _ in 0..2 {
        consume(s);
    }
}
//@ expect: E0382
