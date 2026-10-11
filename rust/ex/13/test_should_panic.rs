fn divide(a: i32, b: i32) -> i32 {
    if b == 0 {
        panic!("0 으로 나눌 수 없다");
    }
    a / b
}

// 패닉해야 통과하는 시험. expected 는 메시지에 들어 있어야 할 글자.
#[test]
#[should_panic(expected = "0 으로")]
fn rejects_zero() {
    divide(1, 0);
}

#[test]
fn divides() {
    assert_eq!(divide(6, 3), 2);
}
//@ test
//@ args: --test-threads=1
