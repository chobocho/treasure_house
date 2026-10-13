fn main() {
    let scores = [Some(70), None, Some(85)];
    let mut total = 0;
    for item in scores {
        if let Some(score) = item {
            total += score;
        }
    }
    println!("{total}");
}
