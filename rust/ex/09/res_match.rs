fn main() {
    for text in ["42", "사십이"] {
        // parse 는 실패할 수 있다 — 그래서 Result 를 돌려준다.
        let parsed: Result<i32, std::num::ParseIntError> = text.parse();
        match parsed {
            Ok(n) => println!("{text} → {n}"),
            Err(e) => println!("{text} → 실패: {e}"),
        }
    }
}
