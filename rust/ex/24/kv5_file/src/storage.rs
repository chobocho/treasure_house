use crate::error::KvError;

// 저장소가 할 줄 아는 일 넷. 항목을 어디에 두든,
// 쓰는 쪽은 이 네 메서드만 안다
pub trait Storage {
    // 키에 값을 둔다. 있던 키면 값이 바뀐다
    fn set(&mut self, key: &str, value: &str) -> Result<(), KvError>;
    // 키의 값을 복제해 돌려준다. 없는 키면 None 이다
    fn get(&self, key: &str) -> Result<Option<String>, KvError>;
    // 키를 지운다. 돌려주는 것은 "있던 키였는가" 다
    fn del(&mut self, key: &str) -> Result<bool, KvError>;
    // 모든 항목을 키의 순서로 돌려준다
    fn list(&self) -> Result<Vec<(String, String)>, KvError>;
}

// 어느 구현이든 지켜야 하는 것. 구현마다 제 시험에서 부른다
#[cfg(test)]
pub fn check_storage(store: &mut dyn Storage) {
    let text = |s: &str| Some(s.to_string());
    // 빈 저장소에서 시작한다
    assert!(store.list().unwrap().is_empty());
    assert_eq!(store.get("a").unwrap(), None);
    assert!(!store.del("a").unwrap());
    // 둔 것을 찾는다
    store.set("b", "2").unwrap();
    store.set("a", "1").unwrap();
    assert_eq!(store.get("a").unwrap(), text("1"));
    // 같은 키에 다시 두면 값이 바뀌고 항목은 늘지 않는다
    store.set("a", "one").unwrap();
    assert_eq!(store.get("a").unwrap(), text("one"));
    assert_eq!(store.list().unwrap().len(), 2);
    // 지우면 없고, 한 번 더 지우면 false 다
    assert!(store.del("b").unwrap());
    assert!(!store.del("b").unwrap());
    assert_eq!(store.get("b").unwrap(), None);
    // 키와 값을 가리지 않는다 — 빈 글, 탭, 줄바꿈, CR
    store.set("", "").unwrap();
    store.set("t\tk", "한 줄\n두 줄\r").unwrap();
    assert_eq!(store.get("").unwrap(), text(""));
    assert_eq!(store.get("t\tk").unwrap(), text("한 줄\n두 줄\r"));
    assert!(store.del("").unwrap());
    assert!(store.del("t\tk").unwrap());
    // list 는 둔 차례가 아니라 키의 바이트 순서다 —
    // 숫자, 대문자, 소문자, 한글
    for key in ["b", "가", "B", "9", "10"] {
        store.set(key, "").unwrap();
    }
    let pairs = store.list().unwrap();
    let keys: Vec<&str> =
        pairs.iter().map(|(key, _)| key.as_str()).collect();
    assert_eq!(keys, ["10", "9", "B", "a", "b", "가"]);
}
