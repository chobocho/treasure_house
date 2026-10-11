fn main() {
    let day = 3;
    let name = match day {
        1 => "월",
        2 => "화",
        3 => "수",
        _ => "모름", // 나머지 전부
    };
    println!("{name}");
}
