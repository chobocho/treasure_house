fn main() {
    for i in 0..3 {
        let doubled = i * 2;
        println!("{doubled}");
    }
    println!("{i}");
}
//@ expect: E0425
