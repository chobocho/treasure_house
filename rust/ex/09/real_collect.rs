fn main() {
    let good = ["1", "2", "3"];
    let bad = ["1", "둘", "3", "넷"];

    // Result 들의 목록을 "목록의 Result" 로 모은다. 첫 오류에서 멈춘다.
    let a: Result<Vec<i32>, _> =
        good.iter().map(|s| s.parse::<i32>()).collect();
    let b: Result<Vec<i32>, _> =
        bad.iter().map(|s| s.parse::<i32>()).collect();
    println!("{a:?}");
    println!("{b:?}");
}
