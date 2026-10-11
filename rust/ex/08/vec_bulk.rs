fn main() {
    let mut v = vec![5, 3, 8, 3, 1, 8, 8];

    v.retain(|x| *x != 1); // 조건에 맞는 것만 남긴다
    println!("{v:?}");
    v.sort();
    println!("{v:?}");
    v.dedup(); // 이웃한 같은 값을 하나로
    println!("{v:?}");
    v.reverse();
    println!("{v:?}");
    println!("{} {:?}", v.contains(&5), v.iter().position(|x| *x == 5));
}
