fn main() {
    let scores = vec![90, 85, 70];

    for s in scores.iter() {
        print!("{s} ");
    }
    println!();

    // for 가 실제로 하는 일을 손으로 쓰면 이렇다.
    let mut it = scores.iter();
    while let Some(s) = it.next() {
        print!("{s} ");
    }
    println!();
}
