use std::marker::PhantomData;

struct User;
struct Order;

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

fn cancel(order: &Id<Order>, by: &Id<User>) {
    println!("사용자 {} 이 주문 {} 을 취소", by.raw, order.raw);
}

fn main() {
    let user: Id<User> = Id::new(7);
    let order: Id<Order> = Id::new(1001);
    // 두 번호를 바꿔 넘겼다.
    cancel(&user, &order);
}
//@ expect: E0308
