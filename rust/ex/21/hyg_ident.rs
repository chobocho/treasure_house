// 변수의 이름을 부르는 쪽이 넘긴다.
macro_rules! make_answer {
    ($name:ident) => {
        let $name = 42;
    };
}

fn main() {
    make_answer!(answer);
    println!("{answer}");
}
