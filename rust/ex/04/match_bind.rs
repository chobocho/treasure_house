fn main() {
    let score = 87;
    let grade = match score {
        90..=100 => 'A',
        80..=89 => 'B',
        n if n < 0 => '?', // 이름으로 받고 조건을 붙일 수도 있다
        _ => 'C',
    };
    println!("{grade}");
}
