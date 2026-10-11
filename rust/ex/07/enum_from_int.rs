enum Level {
    Low,
    Mid,
    High,
}

fn main() {
    let n = 1;
    let l = n as Level;
    println!("{}", l as u8);
}
//@ expect: E0605
