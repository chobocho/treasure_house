fn consume(s: String) {
    println!("{s}");
}

fn main() {
    let s = String::from("hello");
    for _ in 0..2 {
        // 돌 때마다 복사본을 만들어 그것을 넘긴다
        consume(s.clone());
    }
    println!("{s} 는 아직 main 의 것");
}
