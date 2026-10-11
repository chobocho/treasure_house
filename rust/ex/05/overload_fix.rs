// 같은 이름을 두 번 쓸 수 없으니 이름에 뜻을 담는다.
fn square_area(side: u32) -> u32 {
    rect_area(side, side)
}

fn rect_area(w: u32, h: u32) -> u32 {
    w * h
}

fn main() {
    println!("{} {}", square_area(3), rect_area(3, 4));
}
