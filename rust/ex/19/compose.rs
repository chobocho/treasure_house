// 함수 둘을 받아, 이어 붙인 함수 하나를 돌려준다.
fn compose<A, B, C>(
    f: impl Fn(A) -> B,
    g: impl Fn(B) -> C,
) -> impl Fn(A) -> C {
    // 돌려줄 클로저가 f 와 g 를 가져가서 붙잡는다.
    move |x| g(f(x))
}

fn main() {
    let len_then_square = compose(str::len, |n: usize| n * n);
    println!("{}", len_then_square("abc"));

    let offset = 10;
    let shift_then_show =
        compose(move |x: i32| x + offset, |x| format!("<{x}>"));
    println!("{}", shift_then_show(5));
    println!("{}", shift_then_show(-10));
}
