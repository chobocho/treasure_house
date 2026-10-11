fn main() {
    let scores = [72, 95, 58];
    let passed: Vec<&i32> = scores.iter().filter(|s| s >= 60).collect();
    println!("{passed:?}");
}
//@ expect: E0308
