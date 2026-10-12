// 중괄호 블록을 통째로 받아 n 번 되풀이한다.
macro_rules! times {
    ($n:literal, $body:block) => {
        for _ in 0..$n $body
    };
}

fn main() {
    let mut total = 0;
    times!(3, {
        total += 10;
    });
    println!("{total}");
}
