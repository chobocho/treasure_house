fn main() {
    let s = String::from("hello");
    let r = &s;

    // 메서드를 부를 때는 * 를 쓰지 않아도 따라간다
    println!("{} {}", (*r).len(), r.len());

    // println! 도 참조가 가리키는 값을 찍는다
    println!("{s} {r}");

    // 참조의 참조여도 마찬가지다
    let rr = &r;
    println!("{} {rr}", rr.len());
}
