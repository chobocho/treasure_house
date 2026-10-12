/// 글을 대문자로 바꾸고 느낌표를 붙인다.
pub fn shout(s: &str) -> String {
    format!("{}!", s.to_uppercase())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn shout_adds_mark() {
        assert_eq!(shout("hi"), "HI!");
    }
}
