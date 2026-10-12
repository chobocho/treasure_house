fn main() {
    let nan = f64::NAN;
    // 정수의 cmp 는 늘 답이 있다
    println!("{:?}", 1.cmp(&2));
    // 실수의 partial_cmp 는 답이 없을 수 있어 Option 이다
    println!("{:?}", 1.0.partial_cmp(&2.0));
    println!("{:?}", 1.0.partial_cmp(&nan));
    // < 와 >= 는 답이 없으면 둘 다 false 다
    println!("{} {}", 1.0 < nan, 1.0 >= nan);
    // total_cmp 는 NaN 에도 자리를 준다
    println!("{:?}", 1.0_f64.total_cmp(&2.0));
    println!("{:?}", 1.0_f64.total_cmp(&nan));

    let mut v = [2.5, nan, 1.0];
    v.sort_by(|a, b| a.total_cmp(b));
    println!("{v:?}");
    // 답이 없는데 unwrap 하면 패닉한다
    v.sort_by(|a, b| a.partial_cmp(b).unwrap());
    println!("{v:?}");
}
//@ exit: 101
