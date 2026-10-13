fn main() {
    let mut labels: Vec<String> = Vec::new();
    for n in 1..=3 {
        let label = format!("{n}번");
        labels.push(label);
    }
    println!("{labels:?}");
}
