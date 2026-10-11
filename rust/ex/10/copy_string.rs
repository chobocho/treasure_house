#[derive(Clone, Copy)]
struct Player {
    name: String,
    score: u32,
}

fn main() {
    let p = Player {
        name: String::from("kim"),
        score: 0,
    };
    println!("{} {}", p.name, p.score);
}
//@ expect: E0204
