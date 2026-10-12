use std::env;
use std::fs::File;
use std::io::{self, BufRead, BufReader, Write};
use std::process::ExitCode;

const USAGE: &str = "사용법: head [-n 줄수] [파일]";

// 명령 줄에서 읽어 낸 것
struct Config {
    lines: usize,
    path: Option<String>,
}

// 인자를 차례로 꺼내 Config 를 채운다. 틀리면 까닭을 돌려준다
fn parse_args(args: &[String]) -> Result<Config, String> {
    let mut config = Config {
        lines: 10,
        path: None,
    };
    let mut rest = args.iter();
    while let Some(arg) = rest.next() {
        if arg == "-n" {
            let Some(text) = rest.next() else {
                return Err(String::from("-n 뒤에 줄 수가 없다"));
            };
            config.lines = text
                .parse()
                .map_err(|e| format!("줄 수 `{text}`: {e}"))?;
        } else if config.path.is_none() {
            config.path = Some(arg.clone());
        } else {
            return Err(format!("남는 인자 `{arg}`"));
        }
    }
    Ok(config)
}

// 앞의 n 줄만 옮긴다. 어디서 읽어 어디에 쓰는지는 모른다
fn head(
    input: impl BufRead,
    out: &mut impl Write,
    n: usize,
) -> io::Result<()> {
    for line in input.lines().take(n) {
        writeln!(out, "{}", line?)?;
    }
    Ok(())
}

fn run(config: &Config) -> Result<(), String> {
    let mut out = io::stdout().lock();
    let done = match &config.path {
        Some(path) => {
            let file =
                File::open(path).map_err(|e| format!("{path}: {e}"))?;
            head(BufReader::new(file), &mut out, config.lines)
        }
        // 파일을 주지 않으면 표준 입력에서 읽는다
        None => head(io::stdin().lock(), &mut out, config.lines),
    };
    done.map_err(|e| e.to_string())
}

fn main() -> ExitCode {
    let args: Vec<String> = env::args().skip(1).collect();
    let config = match parse_args(&args) {
        Ok(config) => config,
        Err(msg) => {
            // 잘못 불렀을 때는 쓰는 법을 알리고 2 로 끝낸다
            eprintln!("head: {msg}");
            eprintln!("{USAGE}");
            return ExitCode::from(2);
        }
    };
    match run(&config) {
        Ok(()) => ExitCode::SUCCESS,
        Err(msg) => {
            eprintln!("head: {msg}");
            ExitCode::FAILURE
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    // 글 몇 개로 인자 목록을 만든다
    fn args(words: &[&str]) -> Vec<String> {
        words.iter().map(|w| w.to_string()).collect()
    }

    #[test]
    fn head_takes_first_lines() {
        // 입력은 &[u8], 출력은 Vec<u8> — 파일도 화면도 쓰지 않는다
        let mut out = Vec::new();
        head("a\nb\nc\n".as_bytes(), &mut out, 2).unwrap();
        assert_eq!(out, "a\nb\n".as_bytes());
    }

    #[test]
    fn head_of_short_input() {
        let mut out = Vec::new();
        head("a\nb".as_bytes(), &mut out, 5).unwrap();
        assert_eq!(String::from_utf8(out).unwrap(), "a\nb\n");
    }

    #[test]
    fn parse_reads_count_and_path() {
        let config =
            parse_args(&args(&["-n", "3", "memo.txt"])).unwrap();
        assert_eq!(config.lines, 3);
        assert_eq!(config.path, Some(String::from("memo.txt")));
    }

    #[test]
    fn parse_rejects_bad_count() {
        assert!(parse_args(&args(&["-n", "two"])).is_err());
    }
}
