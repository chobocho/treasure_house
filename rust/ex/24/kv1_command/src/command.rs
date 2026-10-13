use std::fmt;

// 명령 한 줄. 키와 값은 줄에서 떼어 만든 새 String 이다
#[derive(Debug, PartialEq)]
pub enum Command {
    Set(String, String),
    Get(String),
    Del(String),
    List,
    // 빈 줄 — 할 일이 없다
    Skip,
}

// 줄을 명령으로 읽지 못한 까닭
#[derive(Clone, Copy, Debug, PartialEq)]
pub enum CmdError {
    // 첫 낱말이 set · get · del · list 가 아니다
    Unknown,
    // 키가 올 자리가 비었다
    NoKey,
    // 키에 빈칸이 들었다
    SpaceInKey,
    // list 뒤에 무엇이 더 있다
    Extra,
}

impl fmt::Display for CmdError {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        let why = match self {
            CmdError::Unknown => "모르는 명령이다",
            CmdError::NoKey => "키가 없다",
            CmdError::SpaceInKey => "키에 빈칸이 있다",
            CmdError::Extra => "list 뒤에 남은 것이 있다",
        };
        write!(f, "{why}")
    }
}

// 키는 비어 있지 않고 빈칸(U+0020)이 없는 글이다
pub fn check_key(key: &str) -> Result<String, CmdError> {
    if key.is_empty() {
        return Err(CmdError::NoKey);
    }
    if key.contains(' ') {
        return Err(CmdError::SpaceInKey);
    }
    Ok(key.to_string())
}

// 줄 하나를 명령으로 읽는다. 첫 빈칸 앞이 명령의 이름이다
pub fn parse_command(line: &str) -> Result<Command, CmdError> {
    if line.is_empty() {
        return Ok(Command::Skip);
    }
    let (name, rest) = line.split_once(' ').unwrap_or((line, ""));
    match name {
        "set" => {
            // 키 뒤의 빈칸 하나 다음부터 줄 끝까지가 값이다
            let (key, value) =
                rest.split_once(' ').unwrap_or((rest, ""));
            Ok(Command::Set(check_key(key)?, value.to_string()))
        }
        "get" => Ok(Command::Get(check_key(rest)?)),
        "del" => Ok(Command::Del(check_key(rest)?)),
        // list 는 그 넉 자뿐인 줄이어야 한다
        "list" if line == "list" => Ok(Command::List),
        "list" => Err(CmdError::Extra),
        _ => Err(CmdError::Unknown),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn set(key: &str, value: &str) -> Result<Command, CmdError> {
        Ok(Command::Set(key.to_string(), value.to_string()))
    }

    fn get(key: &str) -> Result<Command, CmdError> {
        Ok(Command::Get(key.to_string()))
    }

    #[test]
    fn four_commands_and_the_empty_line() {
        assert_eq!(parse_command("set name 보리"), set("name", "보리"));
        assert_eq!(parse_command("get name"), get("name"));
        assert_eq!(
            parse_command("del name"),
            Ok(Command::Del("name".to_string()))
        );
        assert_eq!(parse_command("list"), Ok(Command::List));
        assert_eq!(parse_command(""), Ok(Command::Skip));
    }

    #[test]
    fn value_is_the_rest_of_the_line() {
        // 값 안의 빈칸은 앞뒤 것까지 그대로다
        assert_eq!(parse_command("set a  b c "), set("a", " b c "));
        // 탭도, 역슬래시와 n 두 글자도 받은 그대로다
        assert_eq!(parse_command("set a x\ty"), set("a", "x\ty"));
        assert_eq!(parse_command("set a x\\ny"), set("a", "x\\ny"));
        // 값이 없으면 빈 값이다. 키 뒤의 빈칸 하나는 값이 아니다
        assert_eq!(parse_command("set a"), set("a", ""));
        assert_eq!(parse_command("set a "), set("a", ""));
        assert_eq!(parse_command("set 길 긴 값"), set("길", "긴 값"));
    }

    #[test]
    fn key_is_not_empty_and_has_no_space() {
        assert_eq!(parse_command("get"), Err(CmdError::NoKey));
        assert_eq!(parse_command("get "), Err(CmdError::NoKey));
        assert_eq!(parse_command("set"), Err(CmdError::NoKey));
        // 빈칸이 둘이면 첫 빈칸 다음이 바로 끝난 키다
        assert_eq!(parse_command("set  x"), Err(CmdError::NoKey));
        assert_eq!(parse_command("get a b"), Err(CmdError::SpaceInKey));
        assert_eq!(parse_command("del a "), Err(CmdError::SpaceInKey));
        // 막는 글자는 U+0020 하나다. 탭과 전각 빈칸은 키의 글자다
        assert_eq!(parse_command("get a\tb"), get("a\tb"));
        assert_eq!(parse_command("get a\u{3000}b"), get("a\u{3000}b"));
        assert_eq!(parse_command("get a=b"), get("a=b"));
    }

    #[test]
    fn name_must_match_exactly() {
        let unknown = Err(CmdError::Unknown);
        assert_eq!(parse_command("SET a 1"), unknown);
        assert_eq!(parse_command(" get a"), unknown);
        assert_eq!(parse_command("get\ta"), unknown);
        assert_eq!(parse_command("ls"), unknown);
        assert_eq!(parse_command(" "), unknown);
        assert_eq!(parse_command("# 메모"), unknown);
        assert_eq!(parse_command("list x"), Err(CmdError::Extra));
        assert_eq!(parse_command("list "), Err(CmdError::Extra));
    }

    #[test]
    fn error_says_why() {
        assert_eq!(CmdError::Unknown.to_string(), "모르는 명령이다");
        assert_eq!(CmdError::NoKey.to_string(), "키가 없다");
        assert_eq!(
            CmdError::SpaceInKey.to_string(),
            "키에 빈칸이 있다"
        );
        assert_eq!(
            CmdError::Extra.to_string(),
            "list 뒤에 남은 것이 있다"
        );
    }
}
