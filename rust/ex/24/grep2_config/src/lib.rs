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
}
