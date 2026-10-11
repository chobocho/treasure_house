fn main() {
    // 클로저 — 이름 없는 함수. 매개변수는 | | 사이에 쓴다.
    let add_one = |x| x + 1;
    let area = |w: u32, h: u32| -> u32 { w * h };
    let hello = || println!("안녕");

    println!("{} {}", add_one(5), area(3, 4));
    hello();
}
