use std::mem::MaybeUninit;

// 정리될 때 이름을 찍는 값
struct Noisy(&'static str);

impl Drop for Noisy {
    fn drop(&mut self) {
        println!("  정리: {}", self.0);
    }
}

fn main() {
    // 네 칸 모두 값이 없는 채로 시작한다.
    let mut buf: [MaybeUninit<Noisy>; 4] =
        [const { MaybeUninit::uninit() }; 4];
    // 앞에서부터 몇 칸을 채웠는지는 따로 센다.
    let mut len = 0;
    for name in ["a", "b"] {
        buf[len].write(Noisy(name));
        len += 1;
    }
    println!("채운 칸 {len}");

    println!("main 끝");
}
