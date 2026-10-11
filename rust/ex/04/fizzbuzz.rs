fn main() {
    for n in 1..=15 {
        // 튜플로 묶어 한 번에 가른다.
        match (n % 3, n % 5) {
            (0, 0) => println!("FizzBuzz"),
            (0, _) => println!("Fizz"),
            (_, 0) => println!("Buzz"),
            _ => println!("{n}"),
        }
    }
}
