use std::fs;
use std::io::{self, BufRead, BufReader, Read, Write};
use std::sync::{Arc, Mutex};
use std::thread::{self, JoinHandle};

mod command;
mod error;
mod file;
mod format;
mod mem;
mod shared;
mod storage;

pub use command::{CmdError, Command, check_key, parse_command};
pub use error::KvError;
pub use file::FileStore;
pub use format::{LineError, decode, encode, escape, unescape};
pub use mem::MemStore;
pub use shared::{Locked, Shared};
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

// 답 하나를 쓴다. 값과 목록은 out 에, 알림은 err 에 쓴다.
// 돌려주는 값은 "알림이었는가" 다
fn write_reply(
    place: &str,
    reply: &Reply,
    out: &mut impl Write,
    err: &mut impl Write,
) -> io::Result<bool> {
    match reply {
        Reply::Done => Ok(false),
        Reply::Value(value) => {
            writeln!(out, "{value}")?;
            Ok(false)
        }
        Reply::Lines(lines) => {
            for line in lines {
                writeln!(out, "{line}")?;
            }
            Ok(false)
        }
        Reply::Missing(key) => {
            writeln!(err, "kv: {place}: 없는 키 {key}")?;
            Ok(true)
        }
        Reply::Bad(e) => {
            writeln!(err, "kv: {place}: {e}")?;
            Ok(true)
        }
    }
}

// 알림을 낸 줄이 하나라도 있으면 1 이다
pub fn exit_code(noted: bool) -> u8 {
    if noted { 1 } else { 0 }
}

// run 이 드는 저장소. 어느 구현인지는 실행 중에 정해진다
pub type AnyStore = Box<dyn Storage>;

// 경로를 받았으면 파일에 두는 저장소를, 아니면 메모리의 것을 연다
pub fn open_store(path: Option<&String>) -> Result<AnyStore, KvError> {
    match path {
        Some(path) => Ok(Box::new(FileStore::open(path)?)),
        None => Ok(Box::new(MemStore::new())),
    }
}

// 명령 파일 하나가 남긴 것 — 답, 알림, 알림이 있었는가
pub type Sheets = (Vec<u8>, Vec<u8>, bool);

// 명령 파일 하나를 끝까지 돌린다. 답과 알림은 화면에 쓰지 않고
// 벡터 둘에 모아서 돌려준다
pub fn work(
    store: &mut dyn Storage,
    name: &str,
    text: &str,
) -> Result<Sheets, KvError> {
    let mut answers = Vec::new();
    let mut notes = Vec::new();
    let mut noted = false;
    for (i, line) in text.lines().enumerate() {
        let reply = answer(store, line)?;
        let place = format!("{name} {}번째 줄", i + 1);
        if write_reply(&place, &reply, &mut answers, &mut notes)? {
            noted = true;
        }
    }
    Ok((answers, notes, noted))
}

// 손잡이 하나를 기다려 일꾼이 돌려준 것을 받는다
fn collect<T>(
    handle: JoinHandle<Result<T, KvError>>,
) -> Result<T, KvError> {
    match handle.join() {
        Ok(result) => result,
        // 일꾼이 패닉했다
        Err(_) => Err(KvError::WorkerPanicked),
    }
}

// 명령 파일들을 한 저장소에 돌리고, 받은 차례대로 쓴다
fn run_scripts(
    store: AnyStore,
    scripts: Vec<(String, String)>,
    out: &mut impl Write,
    err: &mut impl Write,
) -> Result<bool, KvError> {
    // 파일마다 일꾼 하나를 띄운다. 일꾼은 Locked 하나씩을 가져간다
    let shared: Shared = Arc::new(Mutex::new(store));
    let mut handles = Vec::new();
    for (name, text) in scripts {
        let mut mine = Locked::new(&shared);
        let job = move || work(&mut mine, &name, &text);
        handles.push(thread::spawn(job));
    }
    // 끝난 차례가 아니라 맡긴 차례로, 모두 기다린다
    let done: Vec<_> = handles.into_iter().map(collect).collect();
    // 다 돌린 다음에 쓴다
    let mut noted = false;
    for sheets in done {
        let (answers, notes, n) = sheets?;
        out.write_all(&answers)?;
        err.write_all(&notes)?;
        noted = noted || n;
    }
    Ok(noted)
}

pub fn run(
    args: &[String],
    stdin: impl Read,
    out: &mut impl Write,
    err: &mut impl Write,
) -> Result<u8, KvError> {
    // 옵션은 없다. 빈 인자와 - 로 시작하는 인자는 받지 않는다
    if args.iter().any(|a| a.is_empty() || a.starts_with('-')) {
        writeln!(err, "쓰는 법: kv [저장소파일 [명령파일 ...]]")?;
        return Ok(2);
    }
    // 첫 인자가 저장소 파일이고, 나머지는 명령 파일이다
    let mut names = args.iter();
    let mut store = open_store(names.next())?;
    // 명령 파일은 일을 시작하기 전에 모두 읽어 둔다
    let mut scripts = Vec::new();
    for name in names {
        let text = fs::read_to_string(name)
            .map_err(|e| KvError::File(name.clone(), e))?;
        scripts.push((name.clone(), text));
    }
    if !scripts.is_empty() {
        let noted = run_scripts(store, scripts, out, err)?;
        return Ok(exit_code(noted));
    }
    // 명령 파일이 없으면 표준 입력의 줄마다 답한다
    let mut noted = false;
    for (i, line) in BufReader::new(stdin).lines().enumerate() {
        let reply = answer(&mut *store, &line?)?;
        let place = format!("{}번째 줄", i + 1);
        if write_reply(&place, &reply, out, err)? {
            noted = true;
        }
    }
    Ok(exit_code(noted))
}

#[cfg(test)]
mod tests {
    use super::*;

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

    #[test]
    fn exit_code_is_one_after_any_notice() {
        assert_eq!(exit_code(false), 0);
        assert_eq!(exit_code(true), 1);
    }

    #[test]
    fn work_collects_answers_and_notes() {
        let mut store = MemStore::new();
        let text = "set a 1\nget a\nget b\n\nlst\nlist\n";
        let (answers, notes, noted) =
            work(&mut store, "t.txt", text).unwrap();
        assert_eq!(String::from_utf8(answers).unwrap(), "1\na\t1\n");
        assert_eq!(
            String::from_utf8(notes).unwrap(),
            "kv: t.txt 3번째 줄: 없는 키 b\n\
             kv: t.txt 5번째 줄: 모르는 명령이다\n"
        );
        assert!(noted);
        // 알림이 없으면 false 다
        let (_, notes, noted) =
            work(&mut store, "t.txt", "get a\n").unwrap();
        assert!(notes.is_empty() && !noted);
    }

    #[test]
    fn panicked_worker_becomes_an_error() {
        let handle = thread::spawn(|| -> Result<u8, KvError> {
            panic!("일꾼이 쓰러졌다");
        });
        assert!(matches!(
            collect(handle),
            Err(KvError::WorkerPanicked)
        ));
        let handle = thread::spawn(|| -> Result<u8, KvError> { Ok(7) });
        assert_eq!(collect(handle).unwrap(), 7);
        let e = KvError::WorkerPanicked.to_string();
        assert_eq!(e, "일꾼이 패닉했다");
    }

    #[test]
    fn workers_write_what_one_after_another_writes() {
        // 키가 겹치지 않는 명령 파일 셋
        let texts = [
            (
                "a.txt",
                "set a.x 1\nget a.x\nget a.y\nset a.x 2\nget a.x\n",
            ),
            ("b.txt", "set b.x 가\ndel b.x\nget b.x\nlst\n"),
            ("c.txt", "get c.x\nset c.x 3\nget c.x\n"),
        ];
        // 한 저장소에 하나씩 차례로 돌린 것
        let mut store = MemStore::new();
        let mut want_out = Vec::new();
        let mut want_err = Vec::new();
        for (name, text) in &texts {
            let (answers, notes, _) =
                work(&mut store, name, text).unwrap();
            want_out.extend(answers);
            want_err.extend(notes);
        }
        // 같은 셋을 일꾼에게 맡긴 것
        let scripts = texts
            .iter()
            .map(|(name, text)| (name.to_string(), text.to_string()))
            .collect();
        let mut out = Vec::new();
        let mut err = Vec::new();
        let store = Box::new(MemStore::new());
        let noted = run_scripts(store, scripts, &mut out, &mut err);
        assert!(noted.unwrap());
        assert_eq!(out, want_out);
        assert_eq!(err, want_err);
    }
}
