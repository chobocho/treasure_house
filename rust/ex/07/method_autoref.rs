struct Rect {
    w: u32,
    h: u32,
}

impl Rect {
    fn area(&self) -> u32 {
        self.w * self.h
    }
}

fn main() {
    let r = Rect { w: 3, h: 4 };
    let by_ref = &r;
    let by_box = Box::new(Rect { w: 1, h: 1 });

    // 점 하나로 다 된다 — 필요한 & 와 * 를 컴파일러가 붙인다.
    println!("{} {} {}", r.area(), by_ref.area(), by_box.area());
    // 메서드는 그냥 함수이기도 하다.
    println!("{}", Rect::area(&r));
}
