use std::collections::HashMap;
use std::env;
use std::fs::File;
use std::io::{self, BufRead, BufReader};
use std::process::ExitCode;

// 기록 파일을 줄마다 읽어 재고를 맞추고, 남은 품목을 찍는다.
fn run(path: &str) -> io::Result<()> {
    let reader = BufReader::new(File::open(path)?);
    let mut stock: HashMap<String, u32> = HashMap::new();
    for record in reader.lines() {
        let record = record?;
        let words: Vec<&str> = record.split_whitespace().collect();
        let [name, kind, qty] = &words[..] else {
            println!("{record}: 낱말이 셋이 아니다");
            continue;
        };
        let qty: u32 = qty.parse().unwrap();
        let have = stock.get(*name).copied().unwrap_or(0);
        if *kind == "in" {
            *stock.entry(name.to_string()).or_insert(0) += qty;
        } else if *kind != "out" {
            println!("{record}: in 도 out 도 아니다");
        } else if have < qty {
            println!("{record}: 모자란다 (지금 {have}개)");
        } else if have == qty {
            stock.remove(*name);
        } else {
            stock.insert(name.to_string(), have - qty);
        }
    }
    let mut left: Vec<(String, u32)> = stock.into_iter().collect();
    left.sort();
    for (name, n) in left {
        println!("{name:<4}{n:>3}");
    }
    Ok(())
}

fn main() -> ExitCode {
    let args: Vec<String> = env::args().collect();
    let [_, path] = &args[..] else {
        eprintln!("쓰는 법: stockroom 파일");
        return ExitCode::from(2);
    };
    if let Err(e) = run(path) {
        eprintln!("stockroom: {path}: {e}");
        return ExitCode::FAILURE;
    }
    ExitCode::SUCCESS
}
