fn main() {
    // format! 은 찍지 않고, 만든 문자열을 돌려준다
    let id = format!("{}-{:03}", "A", 7);
    println!("{id}");
    // 돌려받은 것은 값이라 다시 서식에 넣을 수 있다
    let line = format!("[{id:>8}]");
    println!("{line}");
}
