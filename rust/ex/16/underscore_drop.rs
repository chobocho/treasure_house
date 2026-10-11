struct Noisy(&'static str);

impl Drop for Noisy {
    fn drop(&mut self) {
        println!("{} 정리", self.0);
    }
}

fn main() {
    let _kept = Noisy("_kept"); // 이름이 있다 — 범위 끝까지 산다
    let _ = Noisy("_"); // 이름이 없다 — 그 자리에서 정리된다
    println!("main 끝");
}
