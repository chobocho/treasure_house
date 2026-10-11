fn main() {
    let a = (1, String::from("one"));
    let b = a;

    println!("{b:?}");
    println!("{a:?}");
}
//@ expect: E0382
