// 구조체: 이것 "그리고" 저것(모두 있다).
// 열거형: 이것 "또는" 저것(하나만 있다).
enum Payment {
    Cash,
    Card { last4: String },
    Transfer { bank: String },
}

struct Order {
    item: String,
    price: u32,
    payment: Payment,
}

fn receipt(o: &Order) -> String {
    let how = match &o.payment {
        Payment::Cash => String::from("현금"),
        Payment::Card { last4 } => format!("카드 ****{last4}"),
        Payment::Transfer { bank } => format!("{bank} 이체"),
    };
    format!("{} {}원 — {how}", o.item, o.price)
}

fn main() {
    let orders = [
        Order {
            item: String::from("책"),
            price: 15000,
            payment: Payment::Cash,
        },
        Order {
            item: String::from("펜"),
            price: 2000,
            payment: Payment::Card {
                last4: String::from("1234"),
            },
        },
        Order {
            item: String::from("의자"),
            price: 90000,
            payment: Payment::Transfer {
                bank: String::from("K"),
            },
        },
    ];
    for o in &orders {
        println!("{}", receipt(o));
    }
}
