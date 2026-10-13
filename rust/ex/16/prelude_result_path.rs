// 경기의 결과 — 표준 라이브러리의 Result 와 이름이 같다
#[derive(Debug)]
enum Result {
    Win,
    Lose,
}

fn judge(score: u32) -> Result {
    if score >= 50 {
        Result::Win
    } else {
        Result::Lose
    }
}

fn parse(text: &str) -> std::result::Result<u32, String> {
    text.parse().map_err(|_| format!("숫자가 아니다: {text}"))
}

fn main() {
    println!("{:?} {:?}", judge(70), judge(10));
    println!("{:?} {:?}", parse("70"), parse("x"));
}
