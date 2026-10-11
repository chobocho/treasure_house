fn sign(n: i32) -> &'static str {
    match n {
        x if x > 0 => "양수",
        x if x < 0 => "음수",
        x if x == 0 => "영",
    }
}

fn main() {
    println!("{}", sign(5));
}
//@ expect: E0004
