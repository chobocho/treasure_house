const WIDTH: usize = 4;

fn blank<const N: usize>() -> [u8; N] {
    [b'.'; N]
}

fn main() {
    // 리터럴과 상수의 이름은 그대로 적는다.
    let a = blank::<8>();
    let b = blank::<WIDTH>();
    // 계산식은 중괄호로 감싼다.
    let c = blank::<WIDTH * 2 + 1>();
    println!("{} {} {}", a.len(), b.len(), c.len());
}
//@ expect: error
