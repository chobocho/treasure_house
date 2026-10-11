//! greeter — 인사말을 만드는 작은 라이브러리.

/// 이름을 받아 인사말을 돌려준다.
pub fn greet(name: &str) -> String {
    format!("안녕, {}!", clean(name))
}

fn clean(name: &str) -> &str {
    name.trim()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn greets_by_name() {
        assert_eq!(greet("Ferris"), "안녕, Ferris!");
    }

    #[test]
    fn trims_spaces() {
        // 비공개 함수 clean 도 여기서는 부를 수 있다.
        assert_eq!(clean("  kim "), "kim");
    }
}
