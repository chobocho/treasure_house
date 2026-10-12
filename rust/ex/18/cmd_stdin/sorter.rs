use std::io;

fn main() -> io::Result<()> {
    // 표준 입력이 끝날 때까지 줄을 모은다
    let mut lines = Vec::new();
    for line in io::stdin().lines() {
        lines.push(line?);
    }
    // 정렬해서 번호를 붙여 내보낸다
    lines.sort();
    for (n, line) in lines.iter().enumerate() {
        println!("{}. {line}", n + 1);
    }
    Ok(())
}
