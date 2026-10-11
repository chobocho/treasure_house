mod store {
    // pub(crate) — 이 크레이트 안에서는 어디서나, 밖에서는 안 보인다.
    pub(crate) fn internal_id() -> u32 {
        42
    }

    pub mod cache {
        // pub(super) — 바로 위 모듈(store)까지만.
        pub(super) fn slot() -> u32 {
            7
        }
    }

    pub fn report() -> String {
        format!("{} {}", internal_id(), cache::slot())
    }
}

fn main() {
    println!("{} / {}", store::report(), store::internal_id());
}
