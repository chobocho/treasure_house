fn main() {
    let name = String::from("ferris");
    let consume = move || name;

    let a = consume();
    let b = consume();
    println!("{a} {b}");
}
//@ expect: E0382
