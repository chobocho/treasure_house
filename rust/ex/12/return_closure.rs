// 클로저를 돌려준다. n 을 가져가야 하므로 move.
fn make_adder(n: i32) -> impl Fn(i32) -> i32 {
    move |x| x + n
}

fn main() {
    let add5 = make_adder(5);
    let add100 = make_adder(100);
    println!("{} {}", add5(1), add100(1));
}
