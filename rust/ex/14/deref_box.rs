fn main() {
    let x: i32 = 5;
    let r = &x;
    let b = Box::new(x);

    // 참조도 Box 도 * 로 따라간다.
    println!("{} {}", *r == 5, *b == 5);
    // 메서드를 부를 때는 * 를 안 써도 알아서 따라간다.
    println!("{} {}", r.pow(2), b.pow(2));
}
