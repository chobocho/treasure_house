// mod 로 이름 공간을 만든다. 밖에서 쓸 것에는 pub 을 붙인다.
mod geometry {
    pub fn area(w: u32, h: u32) -> u32 {
        w * h
    }

    pub fn perimeter(w: u32, h: u32) -> u32 {
        double(w + h)
    }

    // pub 이 없다 — 이 모듈 안에서만 쓰는 도우미.
    fn double(n: u32) -> u32 {
        n * 2
    }
}

fn main() {
    println!("{}", geometry::area(3, 4));
    println!("{}", geometry::perimeter(3, 4));
}
