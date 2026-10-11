struct Guard(&'static str);

impl Drop for Guard {
    fn drop(&mut self) {
        println!("{} 정리", self.0);
    }
}

fn inner() {
    let _g = Guard("inner");
    panic!("문제 발생");
}

fn main() {
    let _g = Guard("main");
    inner();
    println!("여기는 오지 않는다");
}
//@ exit: 101
