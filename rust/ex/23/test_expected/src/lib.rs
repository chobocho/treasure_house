/// 글을 나이로 바꾼다. 수가 아니거나 150 을 넘으면 패닉한다.
pub fn parse_age(text: &str) -> u8 {
    let age: u8 = text.parse().expect("수가 아니다");
    if age > 150 {
        panic!("나이가 너무 많다: {age}");
    }
    age
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    #[should_panic(expected = "너무 많다")]
    fn too_old() {
        parse_age("200");
    }

    // 패닉은 하지만 3번 줄의 것이다 — 메시지가 다르다.
    #[test]
    #[should_panic(expected = "너무 많다")]
    fn not_a_number() {
        parse_age("abc");
    }

    // 150 은 넘지 않았다 — 패닉하지 않는다.
    #[test]
    #[should_panic(expected = "너무 많다")]
    fn exactly_150() {
        parse_age("150");
    }
}
