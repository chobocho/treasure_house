fn main() {
    let mut labels: Vec<&str> = Vec::new();
    for n in 1..=3 {
        let label = format!("{n}번");
        labels.push(&label);
    }
    println!("{labels:?}");
}
//@ expect: E0597
