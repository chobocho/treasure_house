enum Coin {
    Won10,
    Won100,
    Won500,
}

// 열거형에도 메서드를 붙인다.
impl Coin {
    fn value(&self) -> u32 {
        match self {
            Coin::Won10 => 10,
            Coin::Won100 => 100,
            Coin::Won500 => 500,
        }
    }
}

fn main() {
    let purse = [Coin::Won500, Coin::Won100, Coin::Won100, Coin::Won10];
    let mut total = 0;
    for c in &purse {
        total += c.value();
    }
    println!("{total}");
}
