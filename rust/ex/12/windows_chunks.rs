fn main() {
    let temps = [20, 22, 21, 25, 24];

    // windows — 겹치며 미끄러지는 조각. 이웃끼리 견줄 때.
    let rises: Vec<i32> =
        temps.windows(2).map(|w| w[1] - w[0]).collect();
    println!("{rises:?}");

    // chunks — 겹치지 않게 끊은 조각.
    for pair in temps.chunks(2) {
        print!("{pair:?} ");
    }
    println!();
}
