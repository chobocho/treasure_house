use std::marker::PhantomData;

// User 에는 아무 derive 도 붙이지 않았다.
struct User;

#[derive(PartialEq)]
struct Id<T> {
    raw: u32,
    kind: PhantomData<T>,
}

impl<T> Id<T> {
    fn new(raw: u32) -> Id<T> {
        Id {
            raw,
            kind: PhantomData,
        }
    }
}

fn main() {
    let a: Id<User> = Id::new(7);
    let b: Id<User> = Id::new(7);
    println!("{}", a == b);
}
//@ expect: E0369
