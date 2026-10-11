use std::ops::Deref;

struct MyBox<T>(T);

// Deref 를 구현하면 내 타입에도 * 를 쓸 수 있다.
impl<T> Deref for MyBox<T> {
    type Target = T;

    fn deref(&self) -> &T {
        &self.0
    }
}

fn main() {
    let b = MyBox(5);
    println!("{}", *b + 1); // *(b.deref()) 와 같다
}
