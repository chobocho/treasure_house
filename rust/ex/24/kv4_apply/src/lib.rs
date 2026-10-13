mod command;
mod error;
mod format;
mod mem;
mod storage;

pub use command::{CmdError, Command, check_key, parse_command};
pub use error::KvError;
pub use format::{LineError, decode, encode, escape, unescape};
pub use mem::MemStore;
pub use storage::Storage;

// 줄 하나에 돌려주는 답
#[derive(Debug, PartialEq)]
pub enum Reply {
    // 찍을 것이 없다 — set, 있던 키의 del, 빈 줄
    Done,
    // get 이 찾은 값
    Value(String),
    // list 의 줄들. 파일에 쓰는 줄과 같은 모양이다
    Lines(Vec<String>),
    // get 이나 del 이 받은 키가 저장소에 없다
    Missing(String),
    // 명령으로 읽지 못한 줄
    Bad(CmdError),
}

// 명령 하나를 저장소에 낸다. 어느 구현인지는 모른다
pub fn apply(
    store: &mut dyn Storage,
    cmd: Command,
) -> Result<Reply, KvError> {
    match cmd {
        Command::Skip => Ok(Reply::Done),
        Command::Set(key, value) => {
            store.set(&key, &value)?;
            Ok(Reply::Done)
        }
        Command::Get(key) => match store.get(&key)? {
            Some(value) => Ok(Reply::Value(value)),
            None => Ok(Reply::Missing(key)),
        },
        Command::Del(key) => {
            if store.del(&key)? {
                Ok(Reply::Done)
            } else {
                Ok(Reply::Missing(key))
            }
        }
        Command::List => {
            let pairs = store.list()?;
            let lines =
                pairs.iter().map(|(k, v)| encode(k, v)).collect();
            Ok(Reply::Lines(lines))
        }
    }
}

// 줄 하나에 답한다. 틀린 줄은 오류가 아니라 답의 한 가지다
pub fn answer(
    store: &mut dyn Storage,
    line: &str,
) -> Result<Reply, KvError> {
    match parse_command(line) {
        Ok(cmd) => apply(store, cmd),
        Err(e) => Ok(Reply::Bad(e)),
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::io;

    // 무엇을 시키든 실패하는 저장소
    struct Down;

    fn down<T>() -> Result<T, KvError> {
        Err(KvError::Io(io::Error::other("꺼진 저장소")))
    }

    impl Storage for Down {
        fn set(&mut self, _: &str, _: &str) -> Result<(), KvError> {
            down()
        }

        fn get(&self, _: &str) -> Result<Option<String>, KvError> {
            down()
        }

        fn del(&mut self, _: &str) -> Result<bool, KvError> {
            down()
        }

        fn list(&self) -> Result<Vec<(String, String)>, KvError> {
            down()
        }
    }

    #[test]
    fn each_line_has_one_reply() {
        let mut store = MemStore::new();
        let mut ask = |line: &str| answer(&mut store, line).unwrap();
        let value = |v: &str| Reply::Value(v.to_string());
        let missing = |k: &str| Reply::Missing(k.to_string());
        assert_eq!(ask("set name 보리"), Reply::Done);
        assert_eq!(ask("get name"), value("보리"));
        assert_eq!(ask("get age"), missing("age"));
        // 같은 키에 다시 두면 값이 바뀐다
        assert_eq!(ask("set name 보리차"), Reply::Done);
        assert_eq!(ask("get name"), value("보리차"));
        // 있던 키를 지우면 찍을 것이 없고, 없는 키면 알릴 것이 있다
        assert_eq!(ask("del name"), Reply::Done);
        assert_eq!(ask("del name"), missing("name"));
        assert_eq!(ask(""), Reply::Done);
        assert_eq!(ask("lst"), Reply::Bad(CmdError::Unknown));
        assert_eq!(ask("get a b"), Reply::Bad(CmdError::SpaceInKey));
    }

    #[test]
    fn list_is_in_byte_order_and_escaped() {
        let mut store = MemStore::new();
        assert_eq!(
            answer(&mut store, "list").unwrap(),
            Reply::Lines(Vec::new())
        );
        let lines = [
            "set name 보리",
            "set Zoo 동물원",
            "set 10 열",
            "set 9 아홉",
            "set 과일 배",
            "set memo a\tb\\c",
        ];
        for line in lines {
            answer(&mut store, line).unwrap();
        }
        let want = [
            "10\t열",
            "9\t아홉",
            "Zoo\t동물원",
            "memo\ta\\tb\\\\c",
            "name\t보리",
            "과일\t배",
        ];
        let want = want.iter().map(|s| s.to_string()).collect();
        assert_eq!(
            answer(&mut store, "list").unwrap(),
            Reply::Lines(want)
        );
    }

    #[test]
    fn store_failure_is_not_a_reply() {
        for line in ["set a 1", "get a", "del a", "list"] {
            let got = answer(&mut Down, line);
            assert!(matches!(got, Err(KvError::Io(_))));
        }
        // 저장소에 가지 않는 줄은 꺼진 저장소에서도 답이 있다
        assert_eq!(answer(&mut Down, "").unwrap(), Reply::Done);
        assert_eq!(
            answer(&mut Down, "lst").unwrap(),
            Reply::Bad(CmdError::Unknown)
        );
    }
}
