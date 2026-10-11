fn main() {
    let mut a = 1;
    if a = 5 {
        println!("다섯");
    }
    a += 1;
    println!("{a}");
}
//@ expect: E0308
