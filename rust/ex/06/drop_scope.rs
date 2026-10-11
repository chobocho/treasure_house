struct Noisy(char);

impl Drop for Noisy {
    // 값이 사라지는 순간에 Rust 가 불러 준다
    fn drop(&mut self) {
        println!("  {} 정리", self.0);
    }
}

fn main() {
    let _a = Noisy('a');
    {
        let _b = Noisy('b');
        println!("안쪽 블록 끝");
    }
    println!("main 끝");
}
