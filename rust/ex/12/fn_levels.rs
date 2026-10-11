// 요구가 적은 쪽부터: FnOnce(한 번) → FnMut(여러 번) → Fn(읽기만).
fn once(f: impl FnOnce() -> usize) -> usize {
    f()
}

fn many_mut(mut f: impl FnMut() -> usize) -> usize {
    f() + f()
}

fn many(f: impl Fn() -> usize) -> usize {
    f() + f()
}

fn main() {
    let names = vec!["kim", "lee"];
    // 읽기만 하는 클로저는 세 자리에 모두 들어간다.
    println!("{}", many(|| names.len()));
    println!("{}", many_mut(|| names.len()));
    println!("{}", once(|| names.len()));

    // 고치는 클로저는 FnMut 와 FnOnce 자리에 들어간다.
    let mut calls = 0;
    let twice = many_mut(|| {
        calls += 1;
        calls
    });
    let third = once(|| {
        calls += 1;
        calls
    });
    println!("{twice} {third}");
}
