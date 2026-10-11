fn main() {
    let mut it = "42+7".chars().peekable();
    let mut number = String::new();

    // peek — 꺼내지 않고 다음 것을 엿본다.
    while let Some(c) = it.peek() {
        if !c.is_ascii_digit() {
            break;
        }
        number.push(*c);
        it.next();
    }
    let rest: String = it.collect();
    println!("{number} / {rest}");
}
