use std::fs::{self, File};
use std::io::{self, BufWriter, Write};

// 한 줄에 "이름 점수" 하나씩 쓴다
fn save(path: &str, scores: &[(String, u32)]) -> io::Result<()> {
    let mut out = BufWriter::new(File::create(path)?);
    for (name, score) in scores {
        writeln!(out, "{name} {score}")?;
    }
    // 실패를 Result 로 받으려고 직접 부른다
    out.flush()
}

// save 가 쓴 모양을 그대로 되읽는다
fn load(path: &str) -> io::Result<Vec<(String, u32)>> {
    let mut scores = Vec::new();
    for line in fs::read_to_string(path)?.lines() {
        let Some((name, score)) = line.split_once(' ') else {
            continue;
        };
        let Ok(score) = score.parse() else { continue };
        scores.push((name.to_string(), score));
    }
    Ok(scores)
}

fn main() -> io::Result<()> {
    let scores =
        vec![(String::from("kim"), 90), (String::from("lee"), 85)];
    save("scores.txt", &scores)?;
    print!("{}", fs::read_to_string("scores.txt")?);
    let back = load("scores.txt")?;
    println!("{back:?}");
    println!("쓴 것과 같은가: {}", back == scores);
    Ok(())
}
