use std::env;
use std::fs::File;
use std::io::{self, BufRead, BufReader};
use std::process::ExitCode;

#[derive(Default)]
struct Counts {
    lines: usize,
    words: usize,
    bytes: usize,
}

// 줄 · 낱말 · 바이트를 센다. 어디서 읽는지는 모른다
fn count(mut input: impl BufRead) -> io::Result<Counts> {
    let mut c = Counts::default();
    let mut line = String::new();
    loop {
        line.clear();
        // read_line 은 줄바꿈까지 담아 준다 — 바이트가 빠지지 않는다
        let n = input.read_line(&mut line)?;
        if n == 0 {
            return Ok(c);
        }
        c.bytes += n;
        c.words += line.split_whitespace().count();
        if line.ends_with('\n') {
            c.lines += 1;
        }
    }
}

fn count_file(path: &str) -> io::Result<Counts> {
    count(BufReader::new(File::open(path)?))
}

fn show(c: &Counts, name: &str) {
    println!("{:>3} {:>3} {:>3} {name}", c.lines, c.words, c.bytes);
}

fn main() -> ExitCode {
    let paths: Vec<String> = env::args().skip(1).collect();
    let mut failed = false;
    if paths.is_empty() {
        // 파일을 주지 않으면 표준 입력을 센다
        match count(io::stdin().lock()) {
            Ok(c) => show(&c, "(표준 입력)"),
            Err(e) => {
                eprintln!("wc: {e}");
                failed = true;
            }
        }
    }
    for path in &paths {
        match count_file(path) {
            Ok(c) => show(&c, path),
            Err(e) => {
                eprintln!("wc: {path}: {e}");
                failed = true;
            }
        }
    }
    if failed {
        ExitCode::FAILURE
    } else {
        ExitCode::SUCCESS
    }
}
