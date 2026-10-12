// 정리될 때 이름을 찍는 값
struct Noisy(&'static str);

impl Drop for Noisy {
    fn drop(&mut self) {
        println!("  정리: {}", self.0);
    }
}

// Copy 가 아닌 두 값을 맞바꾼다.
fn swap_noisy(a: &mut Noisy, b: &mut Noisy) {
    let pa = &raw mut *a;
    let pb = &raw mut *b;
    // 안전: 두 포인터는 서로 다른 가변 참조에서 왔다. 그래서 유효하고,
    // 정렬이 맞고, 값이 들어 있고, 서로 겹치지 않는다. read 는 값을
    // 복사해 꺼낼 뿐 원래 자리를 비우지 않으므로, 꺼낸 자리는 곧바로
    // write 로 덮는다. 세 줄이 끝나면 값은 다시 자리마다 하나씩이다.
    unsafe {
        let tmp = pa.read();
        pa.write(pb.read());
        pb.write(tmp);
    }
}

fn main() {
    let mut x = Noisy("x");
    let mut y = Noisy("y");
    swap_noisy(&mut x, &mut y);
    println!("{} {}", x.0, y.0);
}
