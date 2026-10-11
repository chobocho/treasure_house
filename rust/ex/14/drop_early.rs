struct Lock(&'static str);

impl Drop for Lock {
    fn drop(&mut self) {
        println!("{} 풀림", self.0);
    }
}

fn main() {
    let lock = Lock("잠금");
    println!("잠근 채로 일한다");
    drop(lock); // 범위가 끝나기 전에 미리 정리한다
    println!("풀고 나서 계속한다");
}
