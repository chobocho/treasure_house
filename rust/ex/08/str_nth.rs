fn main() {
    let s = "가나다라";

    // n 번째 글자는 앞에서부터 세어야 안다 — O(n).
    println!("{:?}", s.chars().nth(1));
    println!("{:?}", s.chars().nth(9));
    println!("{:?}", s.chars().last());
    let reversed: String = s.chars().rev().collect();
    println!("{reversed}");
    // 글자 단위로 자르기.
    let head: String = s.chars().take(2).collect();
    println!("{head}");
}
