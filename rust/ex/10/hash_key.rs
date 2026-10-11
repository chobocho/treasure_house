use std::collections::HashSet;

// 해시 집합·맵의 키가 되려면 Hash 와 Eq 가 필요하다.
#[derive(Debug, PartialEq, Eq, Hash, Clone, Copy)]
struct Cell {
    row: u8,
    col: u8,
}

fn main() {
    let mut visited = HashSet::new();
    visited.insert(Cell { row: 0, col: 0 });
    visited.insert(Cell { row: 0, col: 1 });
    visited.insert(Cell { row: 0, col: 0 }); // 이미 있다

    println!("{}", visited.len());
    println!("{}", visited.contains(&Cell { row: 0, col: 1 }));
}
