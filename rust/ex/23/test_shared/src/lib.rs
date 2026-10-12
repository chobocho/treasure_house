use std::fs;

/// 파일에 이름 한 줄을 적고, 적힌 것을 다시 읽어 돌려준다.
pub fn take_seat(file: &str, name: &str) -> String {
    fs::write(file, format!("{name}\n")).unwrap();
    fs::read_to_string(file).unwrap()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn zebra() {
        assert_eq!(take_seat("seat.txt", "zebra"), "zebra\n");
    }

    #[test]
    fn apple() {
        assert_eq!(take_seat("seat.txt", "apple"), "apple\n");
    }

    #[test]
    fn mango() {
        assert_eq!(take_seat("seat.txt", "mango"), "mango\n");
    }
}
