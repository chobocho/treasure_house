// Option 과 Result 가 바로 이런 모양이다.
#[derive(Debug)]
enum Maybe<T> {
    Just(T),
    Nothing,
}

fn first<T: Copy>(xs: &[T]) -> Maybe<T> {
    if xs.is_empty() {
        Maybe::Nothing
    } else {
        Maybe::Just(xs[0])
    }
}

fn main() {
    println!("{:?}", first(&[7, 8]));
    println!("{:?}", first(&["a"]));
    println!("{:?}", first::<f64>(&[]));
}
