enum Cmd {
    Move(i32, i32),
    Stop,
}

fn main() {
    for cmd in [Cmd::Move(3, 4), Cmd::Stop] {
        match cmd {
            Cmd::Move(x, y) => println!("{x}, {y} 만큼"),
            Cmd::Stop => println!("멈춤"),
        }
    }
}
