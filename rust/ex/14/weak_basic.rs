use std::rc::{Rc, Weak};

fn main() {
    let strong = Rc::new(String::from("값"));
    let weak: Weak<String> = Rc::downgrade(&strong); // 주인이 아닌 참조

    println!(
        "{} / {}",
        Rc::strong_count(&strong),
        Rc::weak_count(&strong)
    );
    // 쓰려면 upgrade — 값이 아직 있으면 Some.
    println!("{:?}", weak.upgrade());

    drop(strong); // 마지막 주인이 사라진다
    println!("{:?}", weak.upgrade());
}
