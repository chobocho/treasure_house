use std::collections::BTreeSet;

fn report(input: &str) {
    let mut scores: Vec<u32> = input
        .split_whitespace()
        .map(|word| word.parse().unwrap())
        .collect();
    scores.sort();
    let (Some(low), Some(high)) =
        (scores.iter().min(), scores.iter().max())
    else {
        println!("점수가 없다");
        return;
    };
    println!("{scores:?}");
    println!("가장 낮은 점수 {low}, 가장 높은 점수 {high}");
    let mean = scores.iter().sum::<u32>() as f64 / scores.len() as f64;
    println!("평균 {mean:.1}, 가운뎃값 {:.1}", median(&scores));
    let set: BTreeSet<u32> = scores.iter().copied().collect();
    let unique: Vec<u32> = set.into_iter().collect();
    println!("서로 다른 점수 {}개 {unique:?}", unique.len());
    println!("그 가운뎃값 {:.1}", median(&unique));
}

// 정렬된 점수의 가운뎃값. 개수가 짝수면 가운데 둘의 평균이다.
fn median(sorted: &[u32]) -> f64 {
    let n = sorted.len();
    if n % 2 == 1 {
        sorted[n / 2] as f64
    } else {
        (sorted[n / 2 - 1] + sorted[n / 2]) as f64 / 2.0
    }
}

fn main() {
    report("70 95 82 100 64 95");
    report("  ");
}
