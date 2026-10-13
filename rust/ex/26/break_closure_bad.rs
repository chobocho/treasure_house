fn main() {
    let scores = [70, 85, 40, 90];
    let mut total = 0;
    scores.iter().for_each(|s| {
        if *s < 50 {
            break;
        }
        total += s;
    });
    println!("{total}");
}
//@ expect: E0267
