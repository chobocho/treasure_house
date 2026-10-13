fn main() {
    let units = [5000, 1000, 500, 100, 50, 10];
    let mut rest = 3_867;
    println!("거스름돈 {rest}원");
    for unit in units {
        let count = rest / unit;
        if count == 0 {
            continue;
        }
        println!("{unit:>5}원 {count}개");
        rest = rest % unit;
    }
    println!("남은 돈 {rest}원");
}
