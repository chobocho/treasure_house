#[must_use]
fn add_tax(price: u32) -> u32 {
    price + price / 10
}

fn main() {
    let price = 1000;
    add_tax(price); // 계산만 하고 결과를 버렸다
    println!("{price}");
}
//@ warnings: show
