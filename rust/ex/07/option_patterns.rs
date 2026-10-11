fn main() {
    let pair: (Option<i32>, Option<i32>) = (Some(3), None);

    // 겹친 Option 도 한 번에.
    let text = match pair {
        (Some(a), Some(b)) => format!("둘 다: {}", a + b),
        (Some(x), None) | (None, Some(x)) => format!("하나만: {x}"),
        (None, None) => String::from("없음"),
    };
    println!("{text}");

    let nested: Option<Option<i32>> = Some(None);
    match nested {
        Some(Some(n)) => println!("{n}"),
        Some(None) => println!("겉은 있고 속은 없다"),
        None => println!("겉도 없다"),
    }
}
