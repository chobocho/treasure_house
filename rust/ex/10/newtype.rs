use std::fmt;

// 내 타입으로 한 겹 감싼다(newtype) — 이제 내 타입이라 구현할 수 있다.
struct Scores(Vec<i32>);

impl fmt::Display for Scores {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(
            f,
            "{}개, 합 {}",
            self.0.len(),
            self.0.iter().sum::<i32>()
        )
    }
}

fn main() {
    println!("{}", Scores(vec![1, 2, 3]));
}
