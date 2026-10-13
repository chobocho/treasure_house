struct Rect {
    width: u32,
    height: u32,
}

fn main() {
    let r = Rect {
        width: 3,
        height: 4,
    };
    println!("{}", r.width * r.height);
}
