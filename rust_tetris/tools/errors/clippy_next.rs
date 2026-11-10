// 이 덱의 Bag 에 처음 붙였던 이름. clippy 가 Iterator::next 와 헷갈린다고 한다.
pub struct Bag {
    queue: Vec<char>,
}

impl Bag {
    pub fn next(&mut self) -> char {
        self.queue.pop().unwrap_or('I')
    }
}

fn main() {
    let mut b = Bag { queue: vec!['T', 'S'] };
    println!("{}", b.next());
}
