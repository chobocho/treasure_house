struct Rect {
    w: u32,
    h: u32,
}

// impl 블록 안의 함수가 메서드다. 첫 매개변수 self 가 "자기 자신".
impl Rect {
    fn area(&self) -> u32 {
        self.w * self.h
    }

    fn is_square(&self) -> bool {
        self.w == self.h
    }
}

fn main() {
    let r = Rect { w: 3, h: 4 };
    println!("{} {}", r.area(), r.is_square());
}
