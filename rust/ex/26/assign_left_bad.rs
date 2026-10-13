fn main() {
    let mut limit = 5;
    println!("{limit}");
    10 = limit;
    println!("{limit}");
}
//@ expect: E0070
