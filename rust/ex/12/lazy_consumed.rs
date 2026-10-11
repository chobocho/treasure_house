fn main() {
    let v = vec![1, 2, 3];
    let doubled: Vec<i32> = v
        .iter()
        .map(|x| {
            println!("{x} 를 두 배로");
            x * 2
        })
        .collect(); // 소비해야 비로소 돈다
    println!("{doubled:?}");
}
