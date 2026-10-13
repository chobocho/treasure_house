fn main() {
    let dates = [
        (2023, 2),
        (2024, 2),
        (1900, 2),
        (2000, 2),
        (2025, 4),
        (2025, 12),
        (2025, 0),
        (2025, 13),
    ];
    for date in dates {
        let (year, month) = date;
        let leap =
            (year % 4 == 0 && year % 100 != 0) || year % 400 == 0;
        let days = match month {
            2 => {
                if leap {
                    29
                } else {
                    28
                }
            }
            4 | 6 | 9 | 11 => 30,
            1..=12 => 31,
            _ => 0,
        };
        if days == 0 {
            println!("{year}년 {month}월: 없는 달");
        } else {
            println!("{year}년 {month}월: {days}일");
        }
    }
}
