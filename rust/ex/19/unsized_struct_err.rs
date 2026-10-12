use std::fmt::Display;

struct Shelf<T> {
    label: &'static str,
    item: Box<T>,
}

fn main() {
    let a: Shelf<str> = Shelf {
        label: "글",
        item: Box::from("hello"),
    };
    let b: Shelf<[u8]> = Shelf {
        label: "바이트",
        item: Box::new([1, 2, 3]),
    };
    let c: Shelf<dyn Display> = Shelf {
        label: "수",
        item: Box::new(7),
    };
    println!("{} {}", a.label, a.item.len());
    println!("{} {}", b.label, b.item.len());
    println!("{} {}", c.label, c.item);
}
//@ expect: E0277
