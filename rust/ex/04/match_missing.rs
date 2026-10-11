fn main() {
    let day = 3;
    let name = match day {
        1 => "월",
        2 => "화",
        3 => "수",
    };
    println!("{name}");
}
//@ expect: E0004
