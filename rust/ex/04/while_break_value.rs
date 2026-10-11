fn main() {
    let mut n = 1;
    let _over = while true {
        n *= 2;
        if n > 100 {
            break n;
        }
    };
    println!("{n}");
}
//@ expect: E0571
