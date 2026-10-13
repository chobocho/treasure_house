fn main() {
    let mut prices = vec![300, 500];
    prices.push(700);
    for p in &prices {
        *p += 100;
    }
    println!("{prices:?}");
}
//@ expect: E0594
