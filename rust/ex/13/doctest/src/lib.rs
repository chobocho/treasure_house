//! mathx — 문서 속 예제가 시험으로 도는 것을 보이는 크레이트.

/// 두 수 가운데 큰 쪽을 돌려준다.
///
/// # Examples
///
/// ```
/// assert_eq!(mathx::larger(3, 8), 8);
/// assert_eq!(mathx::larger(5, 5), 5);
/// ```
pub fn larger(a: i32, b: i32) -> i32 {
    if a >= b { a } else { b }
}

/// 0 으로 나누면 패닉한다.
///
/// ```should_panic
/// mathx::divide(1, 0);
/// ```
pub fn divide(a: i32, b: i32) -> i32 {
    a / b
}
