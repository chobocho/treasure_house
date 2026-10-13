enum Entry {
    Item { name: String, price: i32, qty: i32 },
    Discount(i32),
    Shipping,
}

impl Entry {
    // 이 줄이 합계에 보태는 금액. 할인은 음수다.
    fn amount(&self) -> i32 {
        match self {
            Entry::Item { price, qty, .. } => *price * *qty,
            Entry::Discount(won) => -*won,
            Entry::Shipping => 3000,
        }
    }

    fn label(&self) -> String {
        match self {
            Entry::Item { name, qty, .. } => format!("{name} x{qty}"),
            Entry::Discount(_) => String::from("할인"),
            Entry::Shipping => String::from("배송비"),
        }
    }
}

fn main() {
    let order = [
        Entry::Item {
            name: String::from("연필"),
            price: 450,
            qty: 3,
        },
        Entry::Item {
            name: String::from("공책"),
            price: 1200,
            qty: 2,
        },
        Entry::Discount(500),
        Entry::Shipping,
    ];
    let mut total = 0;
    for entry in &order {
        println!("{:>6} {}", entry.amount(), entry.label());
        total += entry.amount();
    }
    println!("{total:>6} 합계");
}
