struct Noisy(char);

impl Drop for Noisy {
    fn drop(&mut self) {
        println!("  {} 정리", self.0);
    }
}

fn work() {
    let _w = Noisy('w');
    println!("work 안");
    // 함수 본문도 스코프다. 닫는 중괄호에서 _w 가 정리된다.
}

fn main() {
    println!("부르기 전");
    work();
    println!("부른 뒤");
}
