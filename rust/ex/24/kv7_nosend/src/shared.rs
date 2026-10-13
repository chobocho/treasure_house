use std::sync::{Arc, Mutex, PoisonError};

use crate::AnyStore;
use crate::error::KvError;
use crate::storage::Storage;

// 일꾼들이 함께 가진 저장소 하나
pub type Shared = Arc<Mutex<AnyStore>>;

// 함께 가진 저장소를 메서드마다 잠갔다 푸는 저장소.
// 일꾼마다 하나씩 가져간다
pub struct Locked {
    shared: Shared,
}

impl Locked {
    pub fn new(shared: &Shared) -> Self {
        Locked {
            shared: Arc::clone(shared),
        }
    }
}

// 독이 든 잠금은 이어 쓰지 않고 오류로 바꾼다
fn poisoned<T>(_: PoisonError<T>) -> KvError {
    KvError::Poisoned
}

// 메서드 하나가 잠금 한 번이다. 열쇠 store 는 메서드가 끝나며
// 사라지므로, 속의 저장소가 일하는 동안 내내 잠겨 있다
impl Storage for Locked {
    fn set(&mut self, key: &str, value: &str) -> Result<(), KvError> {
        let mut store = self.shared.lock().map_err(poisoned)?;
        store.set(key, value)
    }

    fn get(&self, key: &str) -> Result<Option<String>, KvError> {
        let store = self.shared.lock().map_err(poisoned)?;
        store.get(key)
    }

    fn del(&mut self, key: &str) -> Result<bool, KvError> {
        let mut store = self.shared.lock().map_err(poisoned)?;
        store.del(key)
    }

    fn list(&self) -> Result<Vec<(String, String)>, KvError> {
        let store = self.shared.lock().map_err(poisoned)?;
        store.list()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::mem::MemStore;
    use crate::storage::check_storage;
    use std::thread;

    fn fresh() -> Shared {
        Arc::new(Mutex::new(Box::new(MemStore::new())))
    }

    #[test]
    fn locked_store_keeps_the_contract() {
        check_storage(&mut Locked::new(&fresh()));
    }

    #[test]
    fn two_handles_are_one_store() {
        let shared = fresh();
        let mut a = Locked::new(&shared);
        let b = Locked::new(&shared);
        a.set("k", "v").unwrap();
        assert_eq!(b.get("k").unwrap(), Some("v".to_string()));
    }

    #[test]
    fn threads_with_their_own_keys_leave_every_key() {
        let shared = fresh();
        let mut handles = Vec::new();
        for id in 0..3 {
            let mut mine = Locked::new(&shared);
            handles.push(thread::spawn(move || {
                for n in 0..50 {
                    let key = format!("w{id}.{n:02}");
                    mine.set(&key, "x").unwrap();
                    // 제 키는 남이 건드리지 않으니 늘 방금 둔 값이다
                    let got = mine.get(&key).unwrap();
                    assert_eq!(got, Some("x".to_string()));
                }
            }));
        }
        for handle in handles {
            handle.join().unwrap();
        }
        // 어느 차례로 돌았든 남는 것은 세 일꾼의 키 150 개다
        let pairs = Locked::new(&shared).list().unwrap();
        let keys: Vec<&str> =
            pairs.iter().map(|(key, _)| key.as_str()).collect();
        assert_eq!(keys.len(), 150);
        assert_eq!(keys.first(), Some(&"w0.00"));
        assert_eq!(keys.last(), Some(&"w2.49"));
    }

    // 읽은 값에 1 을 더한 글
    fn plus_one(seen: Option<String>) -> String {
        let n: u32 = seen.and_then(|s| s.parse().ok()).unwrap_or(0);
        (n + 1).to_string()
    }

    #[test]
    fn read_then_write_is_two_locks() {
        // 두 일꾼이 저마다 "n 을 읽고, 1 을 더해, 다시 둔다" 고 하자.
        // get 과 set 은 메서드가 따로라서 잠금도 따로다.
        // 스레드는 만들지 않고, 끼어든 차례 하나를 손으로 적는다
        let shared = fresh();
        let mut a = Locked::new(&shared);
        let mut b = Locked::new(&shared);
        a.set("n", "0").unwrap();
        // a 가 0 을 읽는다
        let seen_a = a.get("n").unwrap();
        // a 가 다시 두기 전에 b 도 0 을 읽는다
        let seen_b = b.get("n").unwrap();
        // 둘 다 1 을 둔다
        a.set("n", &plus_one(seen_a)).unwrap();
        b.set("n", &plus_one(seen_b)).unwrap();
        // 두 번 올렸는데 2 가 아니라 1 이다
        assert_eq!(a.get("n").unwrap(), Some("1".to_string()));
    }

    #[test]
    fn poisoned_lock_is_an_error_not_a_panic() {
        let shared = fresh();
        let other = Arc::clone(&shared);
        // 열쇠를 쥔 채 패닉하는 스레드. kv 의 코드에는 이런 길이
        // 없어서 시험이 손으로 만든다
        let handle = thread::spawn(move || {
            let _guard = other.lock().unwrap();
            panic!("열쇠를 쥔 채 쓰러졌다");
        });
        assert!(handle.join().is_err());
        let mut store = Locked::new(&shared);
        assert!(matches!(store.set("a", "1"), Err(KvError::Poisoned)));
        assert!(matches!(store.get("a"), Err(KvError::Poisoned)));
        assert!(matches!(store.del("a"), Err(KvError::Poisoned)));
        assert!(matches!(store.list(), Err(KvError::Poisoned)));
        let e = KvError::Poisoned.to_string();
        assert_eq!(e, "독이 든 잠금을 만났다");
    }
}
