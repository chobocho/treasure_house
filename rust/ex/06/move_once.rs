struct Noisy(char);

impl Drop for Noisy {
    fn drop(&mut self) {
        println!("  {} 정리", self.0);
    }
}

fn main() {
    let a = Noisy('x');
    let b = a; // 주인이 a 에서 b 로 바뀐다
    println!("이름은 둘, 값은 {} 하나", b.0);
}
