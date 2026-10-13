trait Entry {
    // 이 줄이 합계에 보태는 금액. 할인은 음수다.
    fn amount(&self) -> i32;
    fn label(&self) -> String;

    // 찍을 한 줄 — 세 타입이 이 본문을 함께 쓴다.
    fn line(&self) -> String {
        format!("{:>6} {}", self.amount(), self.label())
    }
}

struct Item {
    name: String,
    price: i32,
    qty: i32,
}
struct Discount(i32);
struct Shipping;

impl Entry for Item {
    fn amount(&self) -> i32 {
        self.price * self.qty
    }
    fn label(&self) -> String {
        format!("{} x{}", self.name, self.qty)
    }
}

impl Entry for Discount {
    fn amount(&self) -> i32 {
        -self.0
    }
    fn label(&self) -> String {
        String::from("할인")
    }
}

impl Entry for Shipping {
    fn amount(&self) -> i32 {
        3000
    }
    fn label(&self) -> String {
        String::from("배송비")
    }
}

fn main() {
    let order: Vec<Box<dyn Entry>> = vec![
        Box::new(Item {
            name: String::from("연필"),
            price: 450,
            qty: 3,
        }),
        Box::new(Item {
            name: String::from("공책"),
            price: 1200,
            qty: 2,
        }),
        Box::new(Discount(500)),
        Box::new(Shipping),
    ];
    let mut total = 0;
    for entry in &order {
        println!("{}", entry.line());
        total += entry.amount();
    }
    println!("{total:>6} 합계");
}
