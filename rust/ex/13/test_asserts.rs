fn is_even(n: i32) -> bool {
    n % 2 == 0
}

#[test]
fn uses_assert() {
    assert!(is_even(4)); // 참이어야 한다
    assert!(!is_even(3), "3 은 짝수가 아니어야 한다");
}

#[test]
fn uses_assert_ne() {
    assert_ne!(is_even(1), is_even(2)); // 서로 달라야 한다
}

#[test]
fn message_shows_values() {
    let n = 7;
    assert!(is_even(n), "{n} 은 짝수가 아니다");
}
//@ test
//@ exit: 101
