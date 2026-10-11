// 열거형 — "이것들 가운데 하나".
#[derive(Debug)]
enum Direction {
    North,
    East,
    South,
    West,
}

fn turn_right(d: Direction) -> Direction {
    match d {
        Direction::North => Direction::East,
        Direction::East => Direction::South,
        Direction::South => Direction::West,
        Direction::West => Direction::North,
    }
}

fn main() {
    let d = turn_right(Direction::North);
    println!("{d:?}");
    println!("{:?}", turn_right(d));
}
