use std::fmt::Display;

struct Span<T> {
    start: T,
    end: T,
}

impl<T> Span<T> {
    fn new(start: T, end: T) -> Self {
        Self { start, end }
    }
}

// 두 구간이 겹치는 부분. 끝은 구간에 들지 않는다.
fn overlap<T: PartialOrd + Copy>(
    a: &Span<T>,
    b: &Span<T>,
) -> Option<Span<T>> {
    let start = if a.start > b.start { a.start } else { b.start };
    let end = if a.end < b.end { a.end } else { b.end };
    if start < end {
        Some(Span::new(start, end))
    } else {
        None
    }
}

fn report<T: PartialOrd + Copy + Display>(a: &Span<T>, b: &Span<T>) {
    print!("{}~{} 와 {}~{}: ", a.start, a.end, b.start, b.end);
    match overlap(a, b) {
        Some(both) => {
            println!("{}~{} 에서 겹친다", both.start, both.end)
        }
        None => println!("겹치지 않는다"),
    }
}

fn main() {
    report(&Span::new(9, 11), &Span::new(10, 12));
    report(&Span::new(9, 11), &Span::new(11, 13));
    report(&Span::new(1.5, 4.5), &Span::new(0.25, 9.5));
    report(&Span::new(1.5, 4.5), &Span::new(5.25, 9.5));
    report(&Span::new('a', 'k'), &Span::new('h', 'z'));
}
