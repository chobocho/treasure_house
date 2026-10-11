fn add(a: i32, b: i32) -> i32 {
    a + b
}

// #[test] 가 붙은 함수는 시험이다. 패닉하지 않으면 통과.
#[test]
fn adds_two_numbers() {
    assert_eq!(add(2, 3), 5);
}

#[test]
fn adds_negative() {
    assert_eq!(add(-2, 2), 0);
}
//@ test
