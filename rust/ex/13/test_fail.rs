fn add(a: i32, b: i32) -> i32 {
    a - b // 버그: 빼고 있다
}

#[test]
fn adds_two_numbers() {
    assert_eq!(add(2, 3), 5);
}
//@ test
//@ exit: 101
