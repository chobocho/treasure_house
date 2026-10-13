// 점수에 등급을 매긴다. 100 을 넘는 점수는 받지 않는다.
fn grade(score: u32) -> char {
    match score {
        90..=100 => 'A',
        80..=89 => 'B',
        70..=79 => 'C',
        0..=69 => 'F',
        _ => panic!("점수는 100 까지다: {score}"),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn a_from_90_to_100() {
        assert_eq!(grade(90), 'A');
        assert_eq!(grade(100), 'A');
    }

    #[test]
    fn just_below_each_line() {
        assert_eq!(grade(89), 'B');
        assert_eq!(grade(79), 'C');
        assert_eq!(grade(69), 'F');
    }

    #[test]
    fn zero_is_f() {
        assert_eq!(grade(0), 'F');
        assert_ne!(grade(70), 'F');
    }

    #[test]
    #[should_panic(expected = "100 까지")]
    fn over_100_panics() {
        grade(101);
    }
}
//@ test
//@ args: --test-threads=1
