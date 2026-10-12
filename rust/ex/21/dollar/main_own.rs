// geom 을 가져다 쓰는 크레이트
use geom::square_area;

// 이 크레이트에도 area 라는 함수가 있다. 하는 일은 다르다.
fn area(w: u32, h: u32) -> u32 {
    2 * (w + h)
}

fn main() {
    println!("{}", square_area!(3));
    println!("{}", area(3, 3));
}
