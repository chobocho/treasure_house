use std::rc::Rc;

struct Noisy(&'static str);

impl Drop for Noisy {
    fn drop(&mut self) {
        println!("{} 정리", self.0);
    }
}

fn main() {
    let a = Rc::new(Noisy("값"));
    let b = Rc::clone(&a);
    drop(a);
    println!("a 를 버렸다 — 아직 b 가 있다");
    drop(b);
    println!("b 도 버렸다");
}
