mod parent {
    fn secret() -> u32 {
        7
    }

    pub mod child {
        pub fn peek() -> u32 {
            // 자식은 부모의 비공개 항목을 볼 수 있다.
            super::secret() + 1
        }
    }
}

fn main() {
    println!("{}", parent::child::peek());
}
