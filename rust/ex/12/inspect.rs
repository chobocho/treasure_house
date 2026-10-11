fn main() {
    let total: i32 = [1, 2, 3, 4]
        .iter()
        .inspect(|x| println!("꺼냄 {x}"))
        .filter(|x| **x % 2 == 0)
        .inspect(|x| println!("  통과 {x}"))
        .map(|x| x * 10)
        .sum();
    println!("{total}");
}
