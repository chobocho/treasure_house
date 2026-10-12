// 정리될 때 이름을 찍는 값
struct Noisy(&'static str);

impl Drop for Noisy {
    fn drop(&mut self) {
        println!("  정리: {}", self.0);
    }
}

fn main() {
    let mut slot = Noisy("a");
    let p = &raw mut slot;

    println!("대입");
    // 안전: p 는 살아 있는 slot 을 가리키고, 그 자리에는 값 a 가 있다.
    // 대입은 옛 값을 정리한 다음 새 값을 넣는다.
    unsafe { *p = Noisy("b") };

    println!("write");
    // 안전: p 는 slot 을 가리키고 정렬이 맞다. write 는 옛 값을
    // 정리하지 않고 그 위에 새 값을 덮어쓴다.
    unsafe { p.write(Noisy("c")) };

    println!("main 끝");
}
