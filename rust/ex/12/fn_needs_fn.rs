fn many(f: impl Fn() -> usize) -> usize {
    f() + f()
}

fn main() {
    let mut calls = 0;
    // 붙잡은 것을 고치는 클로저를 Fn 자리에 넘긴다.
    let total = many(|| {
        calls += 1;
        calls
    });
    println!("{total}");
}
//@ expect: E0594
