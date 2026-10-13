#[derive(Debug, PartialEq, Eq, PartialOrd, Ord)]
struct Card {
    rank: u8,
    suit: char,
}

// 줄 세우고, 이웃한 같은 것은 하나만 남긴다.
fn sorted_unique<T: Ord>(mut items: Vec<T>) -> Vec<T> {
    items.sort();
    items.dedup();
    items
}

fn main() {
    let hand = vec![
        Card { rank: 9, suit: 'S' },
        Card { rank: 3, suit: 'H' },
        Card { rank: 5, suit: 'D' },
        Card { rank: 9, suit: 'C' },
        Card { rank: 3, suit: 'H' },
    ];
    let hand = sorted_unique(hand);
    for card in &hand {
        println!("{card:?}");
    }
    println!("{:?}", sorted_unique(vec![20, 4, 20, 15]));
}
