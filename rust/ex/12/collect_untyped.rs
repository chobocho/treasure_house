fn main() {
    let doubled = [1, 2, 3].iter().map(|x| x * 2).collect();
    println!("{doubled:?}");
}
//@ expect: E0283
