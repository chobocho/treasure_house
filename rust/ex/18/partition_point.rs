fn main() {
    // 점수순으로 정렬해 둔 (점수, 이름)
    let ranked = [
        (55, "choi"),
        (60, "kim"),
        (60, "lee"),
        (72, "park"),
        (90, "yoon"),
    ];
    // 조건이 참에서 거짓으로 바뀌는 첫 자리를 준다
    let lo = ranked.partition_point(|&(score, _)| score < 60);
    let hi = ranked.partition_point(|&(score, _)| score <= 80);
    println!("{lo} {hi}");
    // 60 점 이상 80 점 이하
    println!("{:?}", &ranked[lo..hi]);
    // 모두 거짓이면 0, 모두 참이면 길이
    println!("{}", ranked.partition_point(|&(score, _)| score < 0));
    println!("{}", ranked.partition_point(|&(score, _)| score < 100));
}
