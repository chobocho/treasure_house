struct Guard;

impl Drop for Guard {
    fn drop(&mut self) {
        println!("Guard 정리");
    }
}

fn main() {
    let _guard = Guard;
    println!("일을 시작한다");
    panic!("더 갈 수 없다");
}
