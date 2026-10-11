fn main() {
    let pair = (String::from("left"), String::from("right"));
    let l = pair.0; // 첫 칸만 옮겨 간다

    // 둘째 칸의 주인은 여전히 pair 다
    println!("{l} {}", pair.1);

    // 둘 다 꺼내려면 한 번에 푼다
    let both = (String::from("a"), String::from("b"));
    let (a, b) = both;
    println!("{a} {b}");
}
