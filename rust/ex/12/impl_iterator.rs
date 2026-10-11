struct Countdown {
    n: u32,
}

// next 하나만 구현하면 반복자가 된다.
impl Iterator for Countdown {
    type Item = u32;

    fn next(&mut self) -> Option<Self::Item> {
        if self.n == 0 {
            None
        } else {
            self.n -= 1;
            Some(self.n + 1)
        }
    }
}

fn main() {
    for n in (Countdown { n: 3 }) {
        print!("{n} ");
    }
    println!("발사");
    // filter, sum 은 구현하지 않았다 — next 위에 지어진 기본 메서드다.
    let total: u32 = Countdown { n: 10 }.filter(|n| n % 2 == 0).sum();
    println!("{total}");
}
