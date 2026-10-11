struct Rect {
    w: u32,
    h: u32,
}

impl Rect {
    // self 가 없는 함수 — 연관 함수. 타입 이름으로 부른다.
    fn new(w: u32, h: u32) -> Self {
        Self { w, h } // Self 는 이 impl 의 타입(Rect)
    }

    fn square(side: u32) -> Self {
        Self::new(side, side)
    }

    fn area(&self) -> u32 {
        self.w * self.h
    }
}

fn main() {
    let a = Rect::new(3, 4);
    let b = Rect::square(5);
    println!("{} {}", a.area(), b.area());
}
