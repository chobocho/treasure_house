// 매크로가 변수 answer 를 만들어 준다고 기대한다.
macro_rules! make_answer {
    () => {
        let answer = 42;
    };
}

fn main() {
    make_answer!();
    println!("{answer}");
}
//@ expect: E0425
