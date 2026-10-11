fn main() {
    let scores = vec![90, 85];
    let mut it = scores.iter();

    // 반복자는 next() 하나로 움직인다. 끝나면 None.
    println!("{:?}", it.next());
    println!("{:?}", it.next());
    println!("{:?}", it.next());
}
