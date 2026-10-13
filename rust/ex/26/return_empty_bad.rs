// 1000원이 안 되면 깎아 주지 않는다
fn discount(price: u32) -> u32 {
    if price < 1000 {
        return;
    }
    price / 10
}

fn main() {
    println!("{} {}", discount(5000), discount(800));
}
//@ expect: E0069
