// FnMut — 부를 때마다 자기가 붙잡은 것을 고칠 수 있는 클로저.
fn repeat(times: u32, mut action: impl FnMut()) {
    for _ in 0..times {
        action();
    }
}

fn main() {
    let mut log = Vec::new();
    repeat(3, || log.push(log.len() * 10));
    println!("{log:?}");
}
