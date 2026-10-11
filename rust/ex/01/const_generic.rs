// N 은 타입이 아니라 값(배열 길이)이다.
fn sum<const N: usize>(xs: [i32; N]) -> i32 {
    let mut total = 0;
    for x in xs {
        total += x;
    }
    total
}

fn main() {
    println!("{}", sum([1, 2, 3]));
    println!("{}", sum([10; 40])); // 길이 40 도 같은 함수로
}
