fn main() {
    let scores = [72, 95, 58, 88, 41];

    // 반복문으로 — 합격자의 평균.
    let mut sum = 0;
    let mut count = 0;
    for s in scores {
        if s >= 60 {
            sum += s;
            count += 1;
        }
    }
    println!("{}", sum / count);

    // 반복자로 — 무엇을 하는지가 한 줄씩 읽힌다.
    let passed: Vec<i32> =
        scores.iter().copied().filter(|s| *s >= 60).collect();
    println!("{}", passed.iter().sum::<i32>() / passed.len() as i32);
}
