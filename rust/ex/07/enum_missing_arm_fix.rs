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
        Coin::Won50 => 50,
    }
}

fn main() {
    let all = [Coin::Won10, Coin::Won100, Coin::Won500, Coin::Won50];
    for c in &all {
        println!("{}", value(c));
    }
}
