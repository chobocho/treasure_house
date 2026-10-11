fn main() {
    let names = ["kim", "lee", "park"];
    let scores = [90, 85];

    // enumerate — (번호, 원소).
    for (i, name) in names.iter().enumerate() {
        print!("{i}:{name} ");
    }
    println!();
    // zip — 두 반복자를 짝짓는다. 짧은 쪽에서 끝난다.
    for (name, score) in names.iter().zip(scores.iter()) {
        print!("{name}={score} ");
    }
    println!();
}
