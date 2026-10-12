use std::process;

struct Temp(&'static str);

impl Drop for Temp {
    fn drop(&mut self) {
        println!("{} 정리", self.0);
    }
}

fn main() {
    let _t = Temp("임시 자료");
    println!("일하다가 문제를 만났다");
    // 여기서 곧바로 끝난다 — main 의 끝까지 가지 않는다
    process::exit(2);
}
//@ exit: 2
