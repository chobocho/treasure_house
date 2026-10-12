use std::fmt;
use std::fs;
use std::io::{self, Read, Write};

pub const USAGE: &str = "쓰는 법: wc [-lwmc] [파일]...";

// 입력 하나에서 센 것. 찍는 차례도 이 차례다
#[derive(Default)]
pub struct Counts {
    pub lines: usize,
    pub words: usize,
    pub chars: usize,
    pub bytes: usize,
}

impl Counts {
    // 합계 줄을 만들 때 쓴다
    fn add(&mut self, other: &Counts) {
        self.lines += other.lines;
        self.words += other.words;
        self.chars += other.chars;
        self.bytes += other.bytes;
    }
}

// 바이트 슬라이스 하나를 센다. 어디서 온 바이트인지는 모른다
pub fn count(bytes: &[u8]) -> Counts {
    Counts {
        // 줄: 줄바꿈 바이트의 수
        lines: bytes.iter().filter(|&&b| b == b'\n').count(),
        // 낱말: ASCII 공백에서 갈라 남는, 비지 않은 조각의 수
        words: bytes
            .split(|b| b.is_ascii_whitespace())
            .filter(|w| !w.is_empty())
            .count(),
        // 글자: 글로 읽히지 않는 바이트는 U+FFFD 로 바꿔 센다
        chars: String::from_utf8_lossy(bytes).chars().count(),
        bytes: bytes.len(),
    }
}

// 명령 줄이 말한 것: 찍을 칸과 셀 파일
#[derive(Debug, Default, PartialEq)]
pub struct Config {
    pub lines: bool,
    pub words: bool,
    pub chars: bool,
    pub bytes: bool,
    pub paths: Vec<String>,
}

pub fn parse_args(args: &[String]) -> Result<Config, String> {
    let mut cfg = Config::default();
    for arg in args {
        match arg.strip_prefix('-') {
            // "-" 하나뿐인 인자는 옵션이 아니라 파일 이름으로 둔다
            Some(flags) if !flags.is_empty() => {
                for flag in flags.chars() {
                    match flag {
                        'l' => cfg.lines = true,
                        'w' => cfg.words = true,
                        'm' => cfg.chars = true,
                        'c' => cfg.bytes = true,
                        _ => {
                            return Err(format!("모르는 옵션 -{flag}"));
                        }
                    }
                }
            }
            _ => cfg.paths.push(arg.clone()),
        }
    }
    // 칸을 하나도 고르지 않았으면 줄 · 낱말 · 바이트
    if !(cfg.lines || cfg.words || cfg.chars || cfg.bytes) {
        cfg.lines = true;
        cfg.words = true;
        cfg.bytes = true;
    }
    Ok(cfg)
}

// 결과 한 줄. 고른 칸만, 수마다 폭 5 로 오른쪽에 붙이고
// 사이에 빈칸 하나. 차례는 늘 줄 · 낱말 · 글자 · 바이트
pub fn format_row(
    c: &Counts,
    cfg: &Config,
    name: Option<&str>,
) -> String {
    let mut cells = Vec::new();
    if cfg.lines {
        cells.push(format!("{:>5}", c.lines));
    }
    if cfg.words {
        cells.push(format!("{:>5}", c.words));
    }
    if cfg.chars {
        cells.push(format!("{:>5}", c.chars));
    }
    if cfg.bytes {
        cells.push(format!("{:>5}", c.bytes));
    }
    if let Some(name) = name {
        cells.push(name.to_string());
    }
    cells.join(" ")
}

// 어느 파일에서 난 io::Error 인지를 함께 담는다
#[derive(Debug)]
pub struct WcError {
    pub path: String,
    pub source: io::Error,
}

impl fmt::Display for WcError {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(f, "{}: {}", self.path, self.source)
    }
}

impl std::error::Error for WcError {}

// 파일 하나를 통째로 읽어 센다
pub fn count_file(path: &str) -> Result<Counts, WcError> {
    let bytes = fs::read(path).map_err(|source| WcError {
        path: path.to_string(),
        source,
    })?;
    Ok(count(&bytes))
}

// 인자를 보고 세어, 결과는 out 에, 알림은 err 에 쓴다.
// 돌려주는 수가 종료 코드다
pub fn run(
    args: &[String],
    mut stdin: impl Read,
    out: &mut impl Write,
    err: &mut impl Write,
) -> io::Result<u8> {
    let cfg = match parse_args(args) {
        Ok(cfg) => cfg,
        Err(msg) => {
            // 잘못 불렀다: 쓰는 법을 알리고 2
            writeln!(err, "wc: {msg}")?;
            writeln!(err, "{USAGE}")?;
            return Ok(2);
        }
    };
    if cfg.paths.is_empty() {
        // 파일을 주지 않으면 표준 입력을 센다
        let mut buf = Vec::new();
        stdin.read_to_end(&mut buf)?;
        writeln!(out, "{}", format_row(&count(&buf), &cfg, None))?;
        return Ok(0);
    }
    let mut total = Counts::default();
    let mut code = 0;
    for path in &cfg.paths {
        match count_file(path) {
            Ok(c) => {
                writeln!(out, "{}", format_row(&c, &cfg, Some(path)))?;
                total.add(&c);
            }
            Err(e) => {
                // 알리고 다음 파일로 간다. 실패는 종료 코드에 남긴다
                writeln!(err, "wc: {e}")?;
                code = 1;
            }
        }
    }
    if cfg.paths.len() > 1 {
        writeln!(out, "{}", format_row(&total, &cfg, Some("total")))?;
    }
    Ok(code)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn line_is_a_newline_byte() {
        assert_eq!(count(b"a\nb\n").lines, 2);
        // 줄바꿈 없이 끝난 마지막 줄은 세지 않는다
        assert_eq!(count(b"a\nb").lines, 1);
        assert_eq!(count(b"").lines, 0);
    }

    #[test]
    fn word_is_a_run_between_ascii_spaces() {
        assert_eq!(count(b"  one two\n\nthree  ").words, 3);
        // 탭 · CR · 쪽 넘김(\x0c)도 가른다
        assert_eq!(count(b"a\tb\rc\x0cd").words, 4);
        // 세로 탭(\x0b)은 ASCII 공백으로 치지 않는다
        assert_eq!(count(b"a\x0bb").words, 1);
        assert_eq!(count(b" \n\t").words, 0);
        // split 만으로는 빈칸 둘 사이의 빈 조각도 나온다
        let pieces = b"a  b".split(|b| b.is_ascii_whitespace());
        assert_eq!(pieces.count(), 3);
    }

    #[test]
    fn bytes_is_the_length() {
        assert_eq!(count(b"a b\n").bytes, 4);
        assert_eq!(count("가 나\n".as_bytes()).bytes, 8);
    }

    #[test]
    fn unicode_space_does_not_split() {
        // U+3000 은 전각 빈칸이다. ASCII 가 아니다
        let text = "가\u{3000}나";
        assert_eq!(count(text.as_bytes()).words, 1);
        // str 의 split_whitespace 는 같은 글을 둘로 가른다
        assert_eq!(text.split_whitespace().count(), 2);
    }

    #[test]
    fn chars_are_fewer_than_bytes_in_korean() {
        let c = count("가 나\n".as_bytes());
        assert_eq!((c.chars, c.bytes), (4, 8));
        // ASCII 뿐이면 둘이 같다
        let c = count(b"a b\n");
        assert_eq!((c.chars, c.bytes), (4, 4));
    }

    #[test]
    fn broken_bytes_become_replacement_chars() {
        // \xff 와 \xfe 는 UTF-8 어디에도 나올 수 없는 바이트다
        assert_eq!(count(b"ok\xff\xfe").chars, 4);
        // '가' 의 세 바이트 가운데 앞의 둘만 있다
        let cut = &"가".as_bytes()[..2];
        assert_eq!(count(cut).chars, 1);
        let seen = String::from_utf8_lossy(cut);
        assert_eq!(seen, "\u{FFFD}");
    }

    // 글 몇 개로 인자 목록을 만든다
    fn args(words: &[&str]) -> Vec<String> {
        words.iter().map(|w| w.to_string()).collect()
    }

    #[test]
    fn no_flag_means_lines_words_bytes() {
        let cfg = parse_args(&args(&["a.txt"])).unwrap();
        let want = Config {
            lines: true,
            words: true,
            chars: false,
            bytes: true,
            paths: args(&["a.txt"]),
        };
        assert_eq!(cfg, want);
    }

    #[test]
    fn flags_may_be_joined_and_mixed_with_paths() {
        let cfg = parse_args(&args(&["-lm", "a", "-c", "-"])).unwrap();
        assert!(cfg.lines && cfg.chars && cfg.bytes && !cfg.words);
        // "-" 는 옵션이 아니라 파일 이름으로 남는다
        assert_eq!(cfg.paths, args(&["a", "-"]));
    }

    #[test]
    fn unknown_flag_is_an_error() {
        let e = parse_args(&args(&["-lx", "a"])).unwrap_err();
        assert_eq!(e, "모르는 옵션 -x");
    }

    #[test]
    fn row_has_width_five_and_fixed_order() {
        let c = count("가 나\n".as_bytes());
        let cfg = parse_args(&args(&["-cmwl"])).unwrap();
        let row = format_row(&c, &cfg, Some("a.txt"));
        assert_eq!(row, "    1     2     4     8 a.txt");
        let cfg = parse_args(&args(&["-m"])).unwrap();
        assert_eq!(format_row(&c, &cfg, None), "    4");
    }

    #[test]
    fn error_keeps_the_path_and_the_kind() {
        let Err(e) = count_file("data/none.txt") else {
            panic!("없는 파일이 읽혔다");
        };
        assert_eq!(e.path, "data/none.txt");
        assert_eq!(e.source.kind(), io::ErrorKind::NotFound);
        assert!(e.to_string().starts_with("data/none.txt: "));
    }
}
