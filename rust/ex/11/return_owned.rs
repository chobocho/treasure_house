// 참조가 아니라 값 자체를 돌려준다 — 소유권이 부른 쪽으로 넘어간다.
fn make() -> String {
    let s = String::from("hello");
    s
}

fn main() {
    println!("{}", make());
}
