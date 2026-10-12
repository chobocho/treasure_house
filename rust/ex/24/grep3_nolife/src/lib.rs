pub const USAGE: &str = "쓰는 법: grep [-iv] 패턴 [파일]...";

// 줄이 패턴을 품었는가. 패턴은 글자 그대로 찾는 글이다
pub fn is_match(line: &str, pattern: &str) -> bool {
    line.contains(pattern)
}

// 명령 줄이 말한 것: 찾을 패턴, 찾을 파일, 켜진 옵션
#[derive(Debug, Default, PartialEq)]
pub struct Config {
    pub pattern: String,
    pub paths: Vec<String>,
    // -i: ASCII 영문자의 대소문자를 가리지 않는다
    pub ignore_case: bool,
    // -v: 패턴이 없는 줄을 고른다
    pub invert: bool,
}

pub fn parse_args(args: &[String]) -> Result<Config, String> {
    let mut cfg = Config::default();
    // 빈 패턴 "" 도 패턴이라서, 없음은 None 으로 가른다
    let mut pattern = None;
    // "--" 를 지났으면 "-" 로 시작해도 옵션이 아니다
    let mut flags_done = false;
    for arg in args {
        match arg.strip_prefix('-') {
            Some("-") if !flags_done => flags_done = true,
            Some(flags) if !flags_done && !flags.is_empty() => {
                for flag in flags.chars() {
                    match flag {
                        'i' => cfg.ignore_case = true,
                        'v' => cfg.invert = true,
                        _ => {
                            return Err(format!("모르는 옵션 -{flag}"));
                        }
                    }
                }
            }
            // 옵션이 아닌 첫 인자가 패턴, 나머지는 파일 이름
            _ if pattern.is_none() => pattern = Some(arg.clone()),
            _ => cfg.paths.push(arg.clone()),
        }
    }
    match pattern {
        Some(pattern) => {
            cfg.pattern = pattern;
            Ok(cfg)
        }
        None => Err("패턴이 없다".to_string()),
    }
}

impl Config {
    // 이 줄을 고르는가
    pub fn selects(&self, line: &str) -> bool {
        let found = if self.ignore_case {
            // -i: 양쪽의 A-Z 만 소문자로 바꿔 견준다
            is_match(
                &line.to_ascii_lowercase(),
                &self.pattern.to_ascii_lowercase(),
            )
        } else {
            is_match(line, &self.pattern)
        };
        // -v: 답을 뒤집는다
        found != self.invert
    }
}

// 글에서 고른 줄을, 1 부터 센 줄 번호와 함께 돌려준다.
// 줄은 새로 만든 글이 아니라 text 를 빌린 조각이다
pub fn search(text: &str, cfg: &Config) -> Vec<(usize, &str)> {
    text.lines()
        .enumerate()
        .filter(|(_, line)| cfg.selects(line))
        .map(|(i, line)| (i + 1, line))
        .collect()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn pattern_is_found_as_plain_text() {
        assert!(is_match("녹은 영어로 rust 다", "rust"));
        // 낱말의 한가운데에 있어도 맞는다
        assert!(is_match("trust", "rust"));
        // 대소문자가 다르면 다른 글이다
        assert!(!is_match("Rust book 을 샀다", "rust"));
        // 특별한 뜻을 가진 글자는 없다. 점은 점만 찾는다
        assert!(is_match("a.c", "."));
        assert!(!is_match("abc", "a.c"));
    }

    #[test]
    fn hangul_is_compared_char_by_char() {
        assert!(is_match("쇠는 비를 맞으면 녹이 슨다", "녹이"));
        // 자모 둘(U+1100 U+1161)로 적은 "가" 는
        // 한 글자 "가"(U+AC00) 와 다른 글이다
        assert!(!is_match("\u{1100}\u{1161}", "\u{AC00}"));
    }

    #[test]
    fn empty_pattern_is_in_every_line() {
        assert!(is_match("abc", ""));
        assert!(is_match("", ""));
        // 빈 줄에 맞는 것은 빈 패턴뿐이다
        assert!(!is_match("", "a"));
    }

    // 인자 목록을 만드는 도우미
    fn args(list: &[&str]) -> Vec<String> {
        list.iter().map(|a| a.to_string()).collect()
    }

    #[test]
    fn first_plain_argument_is_the_pattern() {
        let cfg = parse_args(&args(&["rust", "a.txt", "b.txt"]));
        let cfg = cfg.unwrap();
        assert_eq!(cfg.pattern, "rust");
        assert_eq!(cfg.paths, ["a.txt", "b.txt"]);
        assert!(!cfg.ignore_case && !cfg.invert);
        // 파일 이름은 없어도 된다
        let cfg = parse_args(&args(&["rust"])).unwrap();
        assert!(cfg.paths.is_empty());
    }

    #[test]
    fn flags_may_come_anywhere() {
        let want = Config {
            pattern: "rust".to_string(),
            paths: vec!["a.txt".to_string()],
            ignore_case: true,
            invert: true,
            ..Config::default()
        };
        let cfg = parse_args(&args(&["-i", "rust", "a.txt", "-v"]));
        assert_eq!(cfg.unwrap(), want);
        // 붙여 써도, 같은 옵션을 거듭 써도 같다
        let cfg = parse_args(&args(&["-vi", "-i", "rust", "a.txt"]));
        assert_eq!(cfg.unwrap(), want);
    }

    #[test]
    fn double_dash_ends_the_flags() {
        let cfg = parse_args(&args(&["-i", "--", "-v", "-x"]));
        let cfg = cfg.unwrap();
        // "--" 뒤의 "-v" 는 패턴이고 "-x" 는 파일 이름이다
        assert_eq!(cfg.pattern, "-v");
        assert_eq!(cfg.paths, ["-x"]);
        assert!(cfg.ignore_case && !cfg.invert);
        // 둘째 "--" 는 글 그대로 패턴이 된다
        let cfg = parse_args(&args(&["--", "--"])).unwrap();
        assert_eq!(cfg.pattern, "--");
        // "-" 하나는 "--" 없이도 옵션이 아니다
        let cfg = parse_args(&args(&["-", "-"])).unwrap();
        assert_eq!(cfg.pattern, "-");
        assert_eq!(cfg.paths, ["-"]);
    }

    #[test]
    fn empty_pattern_is_not_a_missing_pattern() {
        assert_eq!(parse_args(&args(&[""])).unwrap().pattern, "");
        let e = parse_args(&args(&[])).unwrap_err();
        assert_eq!(e, "패턴이 없다");
        // 옵션만 있고 패턴이 없다
        let e = parse_args(&args(&["-i", "--"])).unwrap_err();
        assert_eq!(e, "패턴이 없다");
    }

    #[test]
    fn unknown_flag_is_an_error() {
        let e = parse_args(&args(&["-ix", "rust"])).unwrap_err();
        assert_eq!(e, "모르는 옵션 -x");
        // 패턴 뒤에 있어도 옵션으로 읽는다
        let e = parse_args(&args(&["rust", "-x"])).unwrap_err();
        assert_eq!(e, "모르는 옵션 -x");
        // "--" 에 글이 더 붙은 것은 옵션 묶음으로 읽힌다
        let e = parse_args(&args(&["--help"])).unwrap_err();
        assert_eq!(e, "모르는 옵션 --");
    }

    // 패턴만 정한 Config
    fn cfg(pattern: &str) -> Config {
        Config {
            pattern: pattern.to_string(),
            ..Config::default()
        }
    }

    const TEXT: &str = "Rust book\nrust\n\ntrust rust\n";

    #[test]
    fn search_numbers_lines_from_one() {
        let hits = search(TEXT, &cfg("rust"));
        assert_eq!(hits, [(2, "rust"), (4, "trust rust")]);
        assert!(search(TEXT, &cfg("go")).is_empty());
        // 빈 패턴은 빈 줄까지 모든 줄을 고른다
        assert_eq!(search(TEXT, &cfg("")).len(), 4);
    }

    #[test]
    fn what_a_line_is() {
        let all = cfg("");
        // 줄바꿈 없이 끝난 마지막 줄도 한 줄이다
        assert_eq!(search("a\nb", &all), [(1, "a"), (2, "b")]);
        // 끝의 줄바꿈 뒤에 빈 줄이 하나 더 생기지 않는다
        assert_eq!(search("a\n", &all), [(1, "a")]);
        // 빈 글에는 줄이 없다
        assert!(search("", &all).is_empty());
        // 줄 끝의 \r\n 은 둘 다 줄에서 빠진다
        assert_eq!(search("a\r\nb\r\n", &all), [(1, "a"), (2, "b")]);
        // \r 하나만으로는 줄이 갈리지 않는다
        assert_eq!(search("a\rb\n", &all), [(1, "a\rb")]);
        // 줄바꿈이 든 패턴은 어느 줄에도 없다
        assert!(search("a\nb\n", &cfg("a\nb")).is_empty());
        // 십만 글자짜리 줄도 한 줄이다
        let long = "x".repeat(100_000) + "rust\n";
        assert_eq!(search(&long, &cfg("rust")).len(), 1);
    }

    #[test]
    fn invert_selects_the_other_lines() {
        let v = Config {
            invert: true,
            ..cfg("rust")
        };
        assert_eq!(search(TEXT, &v), [(1, "Rust book"), (3, "")]);
        // 빈 패턴은 모든 줄에 있으므로, 뒤집으면 고를 줄이 없다
        let none = Config {
            invert: true,
            ..cfg("")
        };
        assert!(search(TEXT, &none).is_empty());
    }

    // 패턴을 정하고 -i 를 켠 Config
    fn icase(pattern: &str) -> Config {
        Config {
            ignore_case: true,
            ..cfg(pattern)
        }
    }

    #[test]
    fn ignore_case_folds_ascii_letters_only() {
        assert_eq!(search(TEXT, &icase("RuSt")).len(), 3);
        // -i 가 없으면 고를 줄이 없다
        assert!(search(TEXT, &cfg("RuSt")).is_empty());
        // Z 다음 바이트는 [ 이고 z 다음 바이트는 { 다.
        // 둘은 영문자가 아니라서 -i 로도 서로 맞지 않는다
        assert_eq!((b'Z' + 1, b'z' + 1), (b'[', b'{'));
        assert!(!icase("[").selects("{"));
        // ASCII 밖의 글자는 그대로 견준다. É 와 é 는 다른 글자다
        assert!(icase("café").selects("CAFé"));
        assert!(!icase("café").selects("CAFÉ"));
        // 전각 영문자 A(U+FF21) 와 a(U+FF41) 도 그렇다
        assert!(!icase("\u{FF41}").selects("\u{FF21}"));
    }
}
