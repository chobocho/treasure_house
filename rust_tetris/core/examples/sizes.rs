//! 타입 크기를 잰다.   cargo run -p tetris-core --example sizes
use std::mem::size_of;
use tetris_core::{Board, Game, Kind, Piece};

fn main() {
    println!("Kind          {:>4} B", size_of::<Kind>());
    println!("Option<Kind>  {:>4} B", size_of::<Option<Kind>>());
    println!("Piece         {:>4} B", size_of::<Piece>());
    println!("Board         {:>4} B", size_of::<Board>());
    println!("Game          {:>4} B", size_of::<Game>());
    println!("&Board        {:>4} B", size_of::<&Board>());
}
