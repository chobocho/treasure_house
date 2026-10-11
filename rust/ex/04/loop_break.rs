fn main() {
    let mut n = 1;
    // loop 는 break 를 만날 때까지 돈다.
    loop {
        n *= 2;
        if n > 100 {
            break;
        }
    }
    println!("{n}");
}
