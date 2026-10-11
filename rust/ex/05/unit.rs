fn log(msg: &str) {
    println!("[log] {msg}");
}

fn log_explicit(msg: &str) -> () {
    println!("[log] {msg}");
}

fn main() {
    let a = log("하나");
    let b = log_explicit("둘");
    println!("{a:?} {b:?} {}", a == b);
}
