use std::fs;
use std::io::ErrorKind;

use crate::error::KvError;
use crate::format::{LineError, decode, encode};
use crate::mem::MemStore;
use crate::storage::Storage;

// 파일에 두는 저장소. 항목은 MemStore 가 들고, 바뀔 때마다
// 전부를 path 의 파일에 다시 쓴다
#[derive(Debug)]
pub struct FileStore {
    path: String,
    mem: MemStore,
}

// 파일에 든 글을 줄마다 항목으로 읽어 MemStore 에 담는다.
// name 은 오류에 적을 파일 이름이다
fn load(name: &str, text: &str) -> Result<MemStore, KvError> {
    let mut mem = MemStore::new();
    for (i, line) in text.lines().enumerate() {
        let n = i + 1;
        let (key, value) = decode(line).map_err(|why| {
            KvError::Corrupt(name.to_string(), n, why)
        })?;
        if mem.get(&key)?.is_some() {
            let why = LineError::Duplicate;
            return Err(KvError::Corrupt(name.to_string(), n, why));
        }
        mem.set(&key, &value)?;
    }
    Ok(mem)
}

impl FileStore {
    // 파일이 있으면 읽어 들이고, 없으면 빈 저장소로 시작한다.
    // 없는 파일을 여기서 만들지는 않는다
    pub fn open(path: &str) -> Result<FileStore, KvError> {
        let text = match fs::read_to_string(path) {
            Ok(text) => text,
            Err(e) if e.kind() == ErrorKind::NotFound => String::new(),
            Err(e) => return Err(KvError::File(path.to_string(), e)),
        };
        let mem = load(path, &text)?;
        Ok(FileStore {
            path: path.to_string(),
            mem,
        })
    }

    // 가진 항목 전부를 한 줄에 하나씩 적어 파일을 통째로 바꾼다
    fn save(&self) -> Result<(), KvError> {
        let mut text = String::new();
        for (key, value) in self.mem.list()? {
            text.push_str(&encode(&key, &value));
            text.push('\n');
        }
        fs::write(&self.path, text)
            .map_err(|e| KvError::File(self.path.clone(), e))
    }
}

impl Storage for FileStore {
    fn set(&mut self, key: &str, value: &str) -> Result<(), KvError> {
        self.mem.set(key, value)?;
        self.save()
    }

    fn get(&self, key: &str) -> Result<Option<String>, KvError> {
        self.mem.get(key)
    }

    fn del(&mut self, key: &str) -> Result<bool, KvError> {
        let had = self.mem.del(key)?;
        // 없던 키면 바뀐 것이 없으니 쓰지 않는다
        if had {
            self.save()?;
        }
        Ok(had)
    }

    fn list(&self) -> Result<Vec<(String, String)>, KvError> {
        self.mem.list()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::storage::check_storage;

    // 시험이 파일을 두는 곳. 빌드 결과가 놓이는 target/ 아래다
    const DIR: &str =
        concat!(env!("CARGO_MANIFEST_DIR"), "/target/kv-test");

    // 시험마다 제 이름의 파일을 쓴다. 남아 있던 것은 지우고 시작한다
    fn fresh(name: &str) -> String {
        fs::create_dir_all(DIR).unwrap();
        let path = format!("{DIR}/{name}.kv");
        let _ = fs::remove_file(&path);
        path
    }

    #[test]
    fn file_store_keeps_the_contract() {
        let path = fresh("contract");
        check_storage(&mut FileStore::open(&path).unwrap());
        fs::remove_file(&path).unwrap();
    }

    #[test]
    fn what_was_set_is_there_after_reopening() {
        let path = fresh("reopen");
        let mut store = FileStore::open(&path).unwrap();
        store.set("name", "보리").unwrap();
        store.set("memo", "a\tb\nc\r").unwrap();
        store.set("Zoo", "").unwrap();
        // 파일에는 키의 순서로, 한 줄에 항목 하나가 있다
        let text = fs::read_to_string(&path).unwrap();
        assert_eq!(text, "Zoo\t\nmemo\ta\\tb\\nc\\r\nname\t보리\n");
        // 같은 파일을 새로 열면 같은 항목이 있다
        let again = FileStore::open(&path).unwrap();
        assert_eq!(again.list().unwrap(), store.list().unwrap());
        let memo = again.get("memo").unwrap();
        assert_eq!(memo, Some("a\tb\nc\r".to_string()));
        fs::remove_file(&path).unwrap();
    }

    #[test]
    fn missing_file_is_an_empty_store() {
        let path = fresh("missing");
        let mut store = FileStore::open(&path).unwrap();
        assert!(store.list().unwrap().is_empty());
        // 열기만 해서는, 없던 키를 지워서는 파일이 생기지 않는다
        assert!(!store.del("a").unwrap());
        assert!(fs::read_to_string(&path).is_err());
        // 처음 바뀔 때 생긴다
        store.set("a", "1").unwrap();
        assert_eq!(fs::read_to_string(&path).unwrap(), "a\t1\n");
        // 마지막 항목을 지우면 빈 파일이 남는다
        assert!(store.del("a").unwrap());
        assert_eq!(fs::read_to_string(&path).unwrap(), "");
        fs::remove_file(&path).unwrap();
    }

    #[test]
    fn load_takes_what_lines_gives() {
        let pairs = |text: &str| load("t.kv", text).unwrap().list();
        let one = ("a".to_string(), "1".to_string());
        let two = ("b".to_string(), "2".to_string());
        assert!(pairs("").unwrap().is_empty());
        // 줄바꿈 없이 끝난 마지막 줄도 항목이다
        let want = [one.clone(), two.clone()];
        assert_eq!(pairs("b\t2\na\t1").unwrap(), want);
        // 줄 끝의 \r\n 은 lines() 가 둘 다 뗀다
        assert_eq!(pairs("a\t1\r\nb\t2\r\n").unwrap(), want);
    }

    // load 가 돌려준 Corrupt 의 세 칸을 꺼낸다
    fn corrupt(text: &str) -> (String, usize, LineError) {
        match load("t.kv", text) {
            Err(KvError::Corrupt(name, line, why)) => (name, line, why),
            other => panic!("Corrupt 가 아니다: {other:?}"),
        }
    }

    #[test]
    fn corrupt_line_is_reported_with_its_number() {
        let name = "t.kv".to_string();
        let got = corrupt("a\t1\nb 2\nc\t3\n");
        assert_eq!(got, (name.clone(), 2, LineError::NoTab));
        // 빈 줄도 항목이 아니다
        let got = corrupt("a\t1\n\nb\t2\n");
        assert_eq!(got, (name.clone(), 2, LineError::NoTab));
        let got = corrupt("a\t1\\x\n");
        assert_eq!(got, (name.clone(), 1, LineError::BadEscape));
        // 같은 키가 또 나오면 뒤의 줄이 틀린 줄이다
        let got = corrupt("a\t1\nb\t2\na\t3\n");
        assert_eq!(got, (name.clone(), 3, LineError::Duplicate));
        // 알림에 찍힐 글
        let e = load("memo.kv", "a 1\n").unwrap_err();
        assert_eq!(e.to_string(), "memo.kv 1번째 줄: 탭이 없다");
        let e = load("memo.kv", "a\t1\na\t2").unwrap_err();
        assert_eq!(e.to_string(), "memo.kv 2번째 줄: 앞에 나온 키다");
    }

    #[test]
    fn unreadable_file_is_an_error_with_its_name() {
        // 글이 아닌 바이트가 든 파일
        let path = fresh("badutf8");
        fs::write(&path, b"a\t\xff\n").unwrap();
        let Err(KvError::File(name, e)) = FileStore::open(&path) else {
            panic!("File 이 아니다");
        };
        assert_eq!(name, path);
        assert_eq!(e.kind(), ErrorKind::InvalidData);
        fs::remove_file(&path).unwrap();
        // 디렉터리
        let Err(KvError::File(name, _)) = FileStore::open(DIR) else {
            panic!("File 이 아니다");
        };
        assert_eq!(name, DIR);
    }

    #[test]
    fn write_failure_comes_back_from_set() {
        // 없는 디렉터리 아래의 경로다. 열 때는 "없는 파일" 이라
        // 빈 저장소로 시작하고, 처음 쓰려는 때에 실패가 돌아온다
        fs::create_dir_all(DIR).unwrap();
        let path = format!("{DIR}/no-such-dir/x.kv");
        let mut store = FileStore::open(&path).unwrap();
        let Err(KvError::File(name, e)) = store.set("a", "1") else {
            panic!("File 이 아니다");
        };
        assert_eq!(name, path);
        assert_eq!(e.kind(), ErrorKind::NotFound);
        // 쓸 일이 없는 del 은 그대로 된다
        assert!(!store.del("b").unwrap());
    }
}
