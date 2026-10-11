fn main() {
    let s1 = String::from("hello");
    let s2 = s1;

    println!("{s2}");
    println!("{s1}");
}
//@ expect: E0382
