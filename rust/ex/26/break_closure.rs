fn main() {
    let scores = [70, 85, 40, 90];
    let mut total = 0;
    for s in scores.iter() {
        if *s < 50 {
            break;
        }
        total += s;
    }
    println!("{total}");
}
