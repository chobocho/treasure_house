fn main() {
    let pair = vec![3, 4];
    if let [a, b] = pair[..] {
        println!("{}", a + b);
    }
}
