fn main() {
    let scores = [Some(70), None, Some(85)];
    let mut total = 0;
    for Some(score) in scores {
        total += score;
    }
    println!("{total}");
}
//@ expect: E0005
