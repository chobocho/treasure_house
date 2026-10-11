fn main() {
    let mut a = String::from("left");
    let mut b = String::from("right");

    // 두 자리의 값을 맞바꾼다
    std::mem::swap(&mut a, &mut b);
    println!("{a} {b}");

    // 새 값을 넣고, 있던 값을 돌려받는다
    let old = std::mem::replace(&mut a, String::from("new"));
    println!("{old} {a}");
}
