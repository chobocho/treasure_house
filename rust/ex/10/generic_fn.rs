// T: PartialOrd + Copy — "견줄 수 있고 복사되는 타입이면 무엇이든".
fn largest<T: PartialOrd + Copy>(xs: &[T]) -> T {
    let mut best = xs[0];
    for &x in xs {
        if x > best {
            best = x;
        }
    }
    best
}

fn main() {
    println!("{}", largest(&[3, 9, 4]));
    println!("{}", largest(&[1.5, 0.2]));
    println!("{}", largest(&['r', 'u', 's', 't']));
}
