// T — "어떤 타입이든". 그런데 아무 타입이나 > 로 견줄 수 있을까?
fn largest<T>(xs: &[T]) -> T {
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
}
//@ expect: E0369
