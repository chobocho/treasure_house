fn quarter(month: u32) -> u32 {
    match (month - 1) / 3 {
        0 => 1,
        1 => 2,
        2 => 3,
        3 => 4,
        // 달은 1 부터 12 까지만 온다고 믿는다
        _ => unreachable!("{month} 월은 없다"),
    }
}

fn main() {
    println!("{}", quarter(5));
    println!("{}", quarter(13));
}
//@ exit: 101
