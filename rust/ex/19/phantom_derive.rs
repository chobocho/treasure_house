use std::marker::PhantomData;

struct User;

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

// derive 대신 손으로 쓴다. T 에 조건을 달지 않았다.
impl<T> PartialEq for Id<T> {
    fn eq(&self, other: &Id<T>) -> bool {
        self.raw == other.raw
    }
}

fn main() {
    let a: Id<User> = Id::new(7);
    let b: Id<User> = Id::new(7);
    let c: Id<User> = Id::new(8);
    println!("{} {}", a == b, a == c);
}
