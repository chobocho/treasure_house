/// # Safety
/// `i` 는 `xs.len()` 보다 작아야 한다.
unsafe fn get_fast(xs: &[i32], i: usize) -> i32 {
    // 범위 검사를 건너뛴다. 약속을 어기면 무슨 일이든 일어날 수 있다.
    unsafe { *xs.get_unchecked(i) }
}

// 검사를 한 번 해 주는 안전한 포장.
fn get_or_zero(xs: &[i32], i: usize) -> i32 {
    if i < xs.len() {
        // 안전: 바로 위에서 i < len 을 확인했다.
        unsafe { get_fast(xs, i) }
    } else {
        0
    }
}

fn main() {
    let xs = [10, 20, 30];
    println!("{} {}", get_or_zero(&xs, 1), get_or_zero(&xs, 9));
}
