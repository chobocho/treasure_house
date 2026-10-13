#[derive(Debug)]
struct Item {
    name: String,
    qty: u32,
    price: u32,
}

impl Item {
    fn new(name: &str, qty: u32, price: u32) -> Self {
        Self {
            name: String::from(name),
            qty,
            price,
        }
    }

    // 남은 것을 모두 판 값
    fn total(&self) -> u32 {
        self.qty * self.price
    }

    // n 개를 꺼낸다. 모자라면 아무것도 꺼내지 않고 false 를 돌려준다.
    fn take(&mut self, n: u32) -> bool {
        if n > self.qty {
            return false;
        }
        self.qty -= n;
        true
    }
}

fn main() {
    let mut pen = Item::new("pen", 12, 300);
    println!("{} {}개, 모두 {}원", pen.name, pen.qty, pen.total());
    println!("5개 꺼내기 {}", pen.take(5));
    println!("9개 꺼내기 {}", pen.take(9));
    println!("7개 꺼내기 {}", pen.take(7));
    println!("{pen:?}");
}
