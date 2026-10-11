fn main() {
    let mut s = String::from("first");
    let t = s; // 여기서부터 s 는 쓸 수 없다

    // 새 값을 넣으면 s 는 그 값의 주인이 되어 다시 쓸 수 있다
    s = String::from("second");
    println!("{t} {s}");
}
