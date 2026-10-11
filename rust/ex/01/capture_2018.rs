struct Player {
    name: String,
    score: u32,
}

fn main() {
    let mut p = Player {
        name: String::from("kim"),
        score: 0,
    };
    let name = &p.name;
    // 클로저 bump 는 p.score 하나만 고친다.
    let mut bump = || p.score += 1;
    bump();
    println!("{} {}", name, p.score);
}
//@ edition: 2018
//@ expect: E0502
