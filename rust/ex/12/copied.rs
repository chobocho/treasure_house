fn main() {
    let scores = [72, 95, 58];

    // iter() 는 &i32 를 내준다. copied() 로 값(i32)의 반복자로 바꾼다.
    let passed: Vec<i32> =
        scores.iter().copied().filter(|s| *s >= 60).collect();
    println!("{passed:?}");

    // 패턴으로 & 를 벗겨도 된다.
    let low: Vec<i32> =
        scores.iter().filter(|&&s| s < 60).copied().collect();
    println!("{low:?}");
}
