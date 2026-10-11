fn total(xs: &[i32]) -> i32 {
    let mut sum = 0;
    for x in xs {
        sum += x;
    }
    sum
}

fn main() {
    let arr = [1, 2, 3];
    let v = vec![10, 20, 30, 40];

    // 배열을 빌린 것
    println!("{}", total(&arr));
    // 벡터를 빌린 것
    println!("{}", total(&v));
    // 벡터의 한 구간
    println!("{}", total(&v[1..3]));
}
