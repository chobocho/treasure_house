fn grade(score: u32) -> char {
    if score > 100 {
        return '?'; // 잘못된 입력은 여기서 바로 돌아간다
    }
    if score >= 90 {
        return 'A';
    }
    'B' // 마지막 값은 return 없이
}

fn main() {
    println!("{} {} {}", grade(95), grade(70), grade(300));
}
