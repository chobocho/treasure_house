fn main() {
    let pair = vec![3, 4];
    let [a, b] = pair;
    println!("{}", a + b);
}
//@ expect: E0529
