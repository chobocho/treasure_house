use std::fmt::Debug;

// 수명과 제네릭 타입을 함께 쓴다 — 수명을 먼저 적는다.
struct Latest<'a, T> {
    value: &'a T,
}

impl<'a, T: Debug> Latest<'a, T> {
    fn show(&self) {
        println!("{:?}", self.value);
    }
}

fn main() {
    let n = 7;
    let v = vec![1, 2, 3];
    Latest { value: &n }.show();
    Latest { value: &v }.show();
}
