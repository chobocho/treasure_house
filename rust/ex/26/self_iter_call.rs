struct Cart {
    prices: Vec<u32>,
    total: u32,
}

impl Cart {
    fn add(&mut self, price: u32) {
        self.total += price;
    }
    fn sum(&mut self) {
        for p in &self.prices {
            self.total += *p;
        }
    }
}

fn main() {
    let prices = vec![300, 500];
    let mut cart = Cart { prices, total: 0 };
    cart.add(100);
    cart.sum();
    println!("{}", cart.total);
}
