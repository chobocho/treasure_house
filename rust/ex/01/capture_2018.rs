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
    // 클로저는 score 만 고치지만, 2018 까지는 p 전체를 빌렸다.
    let mut bump = || p.score += 1;
    bump();
    println!("{} {}", name, p.score);
}
//@ edition: 2018
//@ expect: E0502
