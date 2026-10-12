use std::fs::File;
use std::io::{self, Write};

// 어디에 쓰는지 모른다 — Write 이기만 하면 된다
fn report(
    out: &mut impl Write,
    scores: &[(&str, u32)],
) -> io::Result<()> {
    writeln!(out, "{:<6}{:>6}", "name", "score")?;
    for (name, score) in scores {
        writeln!(out, "{name:<6}{score:>6}")?;
    }
    let sum: u32 = scores.iter().map(|(_, s)| s).sum();
    let mean = f64::from(sum) / scores.len() as f64;
    writeln!(out, "{:<6}{mean:>6.1}", "mean")
}

fn main() -> io::Result<()> {
    let scores = [("kim", 90), ("lee", 85), ("park", 100)];
    report(&mut io::stdout(), &scores)?;
    // 같은 함수에 이번에는 파일을 넘긴다
    let mut file = File::create("scores.txt")?;
    report(&mut file, &scores)?;
    Ok(())
}
