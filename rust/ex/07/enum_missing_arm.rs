enum Coin {
    Won10,
    Won100,
    Won500,
    Won50, // 나중에 더한 변형
}

fn value(c: &Coin) -> u32 {
    match c {
        Coin::Won10 => 10,
        Coin::Won100 => 100,
        Coin::Won500 => 500,
    }
}

fn main() {
    println!("{}", value(&Coin::Won50));
}
//@ expect: E0004
