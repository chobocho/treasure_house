// 연관 타입 — 구현하는 쪽이 정하는 타입.
trait Container {
    type Item;

    fn first(&self) -> Option<&Self::Item>;
    fn size(&self) -> usize;
}

struct Stack {
    items: Vec<String>,
}

impl Container for Stack {
    type Item = String; // 이 구현에서는 String

    fn first(&self) -> Option<&String> {
        self.items.first()
    }
    fn size(&self) -> usize {
        self.items.len()
    }
}

fn describe<C: Container>(c: &C) -> String
where
    C::Item: std::fmt::Debug,
{
    format!("{}개, 첫째 {:?}", c.size(), c.first())
}

fn main() {
    let s = Stack {
        items: vec![String::from("a"), String::from("b")],
    };
    println!("{}", describe(&s));
}
