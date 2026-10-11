// 확장 트레이트 — 남의 타입에 내 메서드를 붙인다.
trait WordCount {
    fn word_count(&self) -> usize;
}

impl WordCount for str {
    fn word_count(&self) -> usize {
        self.split_whitespace().count()
    }
}

fn main() {
    println!("{}", "rust is fun".word_count());
    println!("{}", String::from("한 낱말").word_count());
}
