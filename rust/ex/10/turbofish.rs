fn zero<T: Default>() -> T {
    T::default()
}

fn main() {
    // 인자에서 T 를 알아낼 수 없을 때는 직접 적는다.
    let a = zero::<i32>();
    let b: String = zero();
    let c = "42".parse::<u8>();
    println!("{a} {b:?} {c:?}");
}
