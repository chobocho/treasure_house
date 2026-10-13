use std::collections::BTreeMap;

use crate::error::KvError;
use crate::storage::Storage;

// 메모리에만 두는 저장소. BTreeMap 이 항목을 키의 순서로 둔다
#[derive(Debug, Default)]
pub struct MemStore {
    map: BTreeMap<String, String>,
}

impl MemStore {
    pub fn new() -> Self {
        MemStore::default()
    }
}

impl Storage for MemStore {
    fn set(&mut self, key: &str, value: &str) -> Result<(), KvError> {
        self.map.insert(key.to_string(), value.to_string());
        Ok(())
    }

    fn get(&self, key: &str) -> Result<Option<String>, KvError> {
        Ok(self.map.get(key).map(|value| value.clone()))
    }

    fn del(&mut self, key: &str) -> Result<bool, KvError> {
        Ok(self.map.remove(key).is_some())
    }

    fn list(&self) -> Result<Vec<(String, String)>, KvError> {
        let pairs = self
            .map
            .iter()
            .map(|(key, value)| (key.clone(), value.clone()))
            .collect();
        Ok(pairs)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::storage::check_storage;

    #[test]
    fn mem_store_keeps_the_contract() {
        check_storage(&mut MemStore::new());
    }
}
