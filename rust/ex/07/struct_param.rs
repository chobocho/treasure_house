struct Rect {
    w: u32,
    h: u32,
}

// 읽기만 한다 — 빌린다.
fn area(r: &Rect) -> u32 {
    r.w * r.h
}

// 고친다 — 가변으로 빌린다.
fn grow(r: &mut Rect, by: u32) {
    r.w += by;
    r.h += by;
}

fn main() {
    let mut r = Rect { w: 3, h: 4 };
    println!("{}", area(&r));
    grow(&mut r, 1);
    println!("{} ({}x{})", area(&r), r.w, r.h);
}
