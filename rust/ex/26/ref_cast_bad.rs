fn main() {
    let scores = vec![70, 85];
    let mut sum = 0.0;
    for s in &scores {
        sum += s as f64;
    }
    println!("{}", sum / 2.0);
}
//@ expect: E0606
