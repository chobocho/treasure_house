// 받은 것을 tt 한 덩이씩 글자로 바꿔 배열에 담는다.
macro_rules! pieces {
    ($($t:tt)*) => {
        [$(stringify!($t)),*]
    };
}

fn main() {
    let a = pieces!(1 + 2 * 3);
    println!("{} {:?}", a.len(), a);
    // 괄호로 묶으면 통째로 한 덩이다.
    let b = pieces!((1 + 2) * 3);
    println!("{} {:?}", b.len(), b);
    // 식이 아닌 것도 받는다.
    let c = pieces!(fn => [a, b] -1.5 'x' <<= {});
    println!("{} {:?}", c.len(), c);
}
