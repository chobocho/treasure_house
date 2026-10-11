/// 두 수 가운데 큰 쪽을 돌려준다.
///
/// 같으면 `a` 를 돌려준다.
fn larger(a: i32, b: i32) -> i32 {
    if a >= b { a } else { b }
}

fn main() {
    println!("{}", larger(3, 8));
}
