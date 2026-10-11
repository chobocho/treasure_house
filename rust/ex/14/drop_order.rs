struct Noisy(&'static str);

impl Drop for Noisy {
    fn drop(&mut self) {
        println!("{} 정리", self.0);
    }
}

fn main() {
    let _a = Noisy("a");
    let _b = Noisy("b");
    {
        let _c = Noisy("c");
        println!("안쪽 블록 끝");
    }
    println!("main 끝");
}
