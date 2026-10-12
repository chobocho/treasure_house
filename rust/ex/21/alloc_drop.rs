use std::alloc::{Layout, alloc, dealloc, handle_alloc_error};
use std::ptr;

// 정리될 때 이름을 찍는 값
struct Noisy(&'static str);

impl Drop for Noisy {
    fn drop(&mut self) {
        println!("  정리: {}", self.0);
    }
}

fn main() {
    let layout = Layout::array::<Noisy>(2).unwrap();
    // 안전: Noisy 는 크기가 있는 타입이라 두 칸의 크기는 0 이 아니다.
    let raw = unsafe { alloc(layout) };
    if raw.is_null() {
        handle_alloc_error(layout);
    }
    let p = raw as *mut Noisy;

    // 안전: 두 칸 모두 얻은 자리 안이고 정렬이 맞다. 아직 값이 없는
    // 자리라서 대입이 아니라 write 로 넣는다.
    unsafe {
        p.write(Noisy("a"));
        p.add(1).write(Noisy("b"));
    }

    println!("drop_in_place");
    // 안전: 0번 칸에는 위에서 넣은 값이 있다. 이 뒤로는 읽지 않는다.
    unsafe { ptr::drop_in_place(p) };

    println!("read");
    // 안전: 1번 칸의 값을 b 로 꺼낸다. 이 뒤로는 읽지 않는다.
    let b = unsafe { p.add(1).read() };

    println!("dealloc");
    // 안전: 두 칸에 남은 값이 없다. 받은 layout 그대로 한 번 돌려준다.
    unsafe { dealloc(raw, layout) };

    println!("main 끝 {}", b.0);
}
