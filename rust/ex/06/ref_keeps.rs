struct Noisy(char);

impl Drop for Noisy {
    fn drop(&mut self) {
        println!("  {} 정리", self.0);
    }
}

// 값을 받는다. 주인이 되므로 여기서 정리한다.
fn take(n: Noisy) {
    println!("take: {}", n.0);
}

// 참조를 받는다. 주인이 아니므로 정리하지 않는다.
fn peek(n: &Noisy) {
    println!("peek: {}", n.0);
}

fn main() {
    let a = Noisy('a');
    let b = Noisy('b');
    take(a);
    peek(&b);
    println!("main 끝");
}
