/// 글에서 가장 긴 낱말을 돌려준다. 길이가 같으면 먼저 나온 것.
pub fn longest(text: &str) -> &str {
    let mut best = "";
    for word in text.split_whitespace() {
        if word.len() > best.len() {
            best = word;
        }
    }
    best
}

/// 글에 든 낱말의 수.
pub fn count(text: &str) -> usize {
    text.split_whitespace().count()
}

#[cfg(test)]
mod tests {
    use super::*;

    // #[test] 가 없는 보통 함수 — 아래 두 시험이 같은 글을 쓴다.
    fn sample() -> &'static str {
        "red green blue"
    }

    #[test]
    fn longest_is_green() {
        assert_eq!(longest(sample()), "green");
    }

    #[test]
    fn counts_three() {
        assert_eq!(count(sample()), 3);
    }
}
