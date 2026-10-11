fn main() {
    let names = vec!["kim", "lee"];
    // 읽기만 한다 — 클로저는 names 를 빌린다.
    let count = || names.len();

    println!("{}", count());
    println!("{names:?}"); // 주인은 여전히 쓸 수 있다
    println!("{}", count());
}
