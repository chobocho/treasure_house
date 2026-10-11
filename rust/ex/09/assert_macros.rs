fn average(xs: &[f64]) -> f64 {
    // 부르는 쪽이 지켜야 할 약속을 코드로 적는다.
    assert!(!xs.is_empty(), "빈 목록의 평균은 없다");
    xs.iter().sum::<f64>() / xs.len() as f64
}

fn main() {
    println!("{}", average(&[1.0, 2.0, 6.0]));
    assert_eq!(1 + 1, 2);
    println!("{}", average(&[]));
}
//@ exit: 101
