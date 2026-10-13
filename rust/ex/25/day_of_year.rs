fn is_leap(year: u32) -> bool {
    (year % 4 == 0 && year % 100 != 0) || year % 400 == 0
}

fn days_in_month(year: u32, month: u32) -> u32 {
    match month {
        2 => {
            if is_leap(year) {
                29
            } else {
                28
            }
        }
        4 | 6 | 9 | 11 => 30,
        1..=12 => 31,
        _ => 0,
    }
}

fn day_of_year(year: u32, month: u32, day: u32) -> u32 {
    // 없는 달이면 days_in_month 가 0 이라 여기서 걸린다
    if day == 0 || day > days_in_month(year, month) {
        return 0;
    }
    let mut total = day;
    for m in 1..month {
        total += days_in_month(year, m);
    }
    total
}

fn report(year: u32, month: u32, day: u32) {
    let n = day_of_year(year, month, day);
    if n == 0 {
        println!("{year}-{month:02}-{day:02} 없는 날짜");
    } else {
        println!("{year}-{month:02}-{day:02} {n}째 날");
    }
}

fn main() {
    report(2025, 1, 1);
    report(2025, 3, 1);
    report(2024, 3, 1);
    report(2024, 12, 31);
    report(2025, 2, 29);
    report(2025, 13, 1);
    report(2025, 6, 0);
}
