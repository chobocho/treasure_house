struct Span {
    start: u32,
    end: u32,
}

impl Span {
    fn new(start: u32, end: u32) -> Self {
        Self { start, end }
    }

    // 두 구간이 겹치는 부분. 끝 시각은 구간에 들지 않는다.
    fn overlap(&self, other: &Span) -> Option<Span> {
        let start = self.start.max(other.start);
        let end = self.end.min(other.end);
        if start < end {
            Some(Span::new(start, end))
        } else {
            None
        }
    }
}

fn report(a: &Span, b: &Span) {
    print!("{}-{}시와 {}-{}시: ", a.start, a.end, b.start, b.end);
    if let Some(Span { start, end }) = a.overlap(b) {
        println!("{start}시부터 {end}시까지 겹친다");
    } else {
        println!("겹치지 않는다");
    }
}

fn main() {
    let morning = Span::new(9, 11);
    report(&morning, &Span::new(10, 12));
    report(&morning, &Span::new(11, 13));
    report(&morning, &Span::new(8, 18));
    report(&morning, &Span::new(14, 15));
}
