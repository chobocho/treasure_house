struct Size {
    w: u32,
    h: u32,
    d: u32,
}

fn main() {
    let size = Size { w: 3, h: 4, d: 5 };
    println!("깊이 {}", size.d);
    let Size { w, h, .. } = size;
    println!("바닥 {}", w * h);
}
