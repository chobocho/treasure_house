fn main() {
    let mut n = 1;
    // break 뒤에 값을 쓰면 loop 식 전체의 값이 된다.
    let first_over_100 = loop {
        n *= 2;
        if n > 100 {
            break n;
        }
    };
    println!("{first_over_100}");
}
