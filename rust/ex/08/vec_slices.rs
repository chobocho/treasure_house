fn total(xs: &[i32]) -> i32 {
    xs.iter().sum()
}

fn main() {
    let v = vec![1, 2, 3, 4, 5];

    // 벡터의 일부를 빌린다 — 슬라이스.
    println!("{} {} {}", total(&v), total(&v[1..3]), total(&v[3..]));
    println!("{:?}", v.split_first());
    println!("{:?}", v.chunks(2).collect::<Vec<_>>());
    println!("{}", v.starts_with(&[1, 2]));
}
