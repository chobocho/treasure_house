fn main() {
    let scores = [90, 85, 70];
    let mut total = 0;
    for s in scores {
        total += s;
    }
    println!("합계 {total}");

    // 번호가 필요하면 enumerate.
    for (i, s) in scores.iter().enumerate() {
        println!("{i}번: {s}");
    }
}
