use std::iter;

fn main() {
    // successors — 앞의 값에서 다음 값을 만든다.
    let powers: Vec<u32> =
        iter::successors(Some(1u32), |x| Some(x * 2))
            .take(8)
            .collect();
    println!("{powers:?}");

    // from_fn — 부를 때마다 다음 값을 내는 클로저로.
    let (mut a, mut b) = (0u32, 1u32);
    let fib: Vec<u32> = iter::from_fn(|| {
        let now = a;
        (a, b) = (b, a + b);
        Some(now)
    })
    .take(10)
    .collect();
    println!("{fib:?}");

    let line: String = iter::repeat("=-").take(5).collect();
    println!("{line}");
}
