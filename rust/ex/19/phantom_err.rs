struct User;
struct Order;

// 속은 u32 하나이고, T 는 무엇의 번호인지만 가른다.
struct Id<T> {
    raw: u32,
}

fn main() {
    let user = Id::<User> { raw: 7 };
    let order = Id::<Order> { raw: 1001 };
    println!("{} {}", user.raw, order.raw);
}
//@ expect: E0392
