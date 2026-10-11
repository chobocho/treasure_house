fn main() {
    let mut stack = vec![1, 2, 3];

    // 패턴이 맞는 동안 돈다 — pop 이 None 을 주면 끝난다.
    while let Some(top) = stack.pop() {
        print!("{top} ");
    }
    println!("비었다");

    let mut chars = "a1b2".chars();
    while let Some(c) = chars.next() {
        if c.is_ascii_digit() {
            print!("[{c}]");
        }
    }
    println!();
}
