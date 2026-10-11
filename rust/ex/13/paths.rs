fn version() -> &'static str {
    "1.0"
}

mod app {
    pub fn banner() -> String {
        // crate:: — 크레이트의 뿌리에서부터. super:: — 한 단계 위.
        format!("{} / {}", crate::version(), super::version())
    }

    pub mod ui {
        pub fn title() -> String {
            // self:: — 지금 모듈. 여기서는 생략해도 같다.
            format!("[{}]", self::name())
        }

        fn name() -> &'static str {
            "demo"
        }
    }
}

fn main() {
    println!("{}", app::banner());
    println!("{}", app::ui::title());
}
