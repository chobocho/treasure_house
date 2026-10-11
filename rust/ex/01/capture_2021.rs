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
    // 클로저는 score 만 고치지만, 2021 부터는 p.score 만 빌린다.
    let mut bump = || p.score += 1;
    bump();
    println!("{} {}", name, p.score);
}
//@ edition: 2021
