use std::cmp::Ordering;

fn hint(guess: u32, answer: u32) -> &'static str {
    // cmp 는 Ordering 의 세 변형 가운데 하나를 돌려준다
    match guess.cmp(&answer) {
        Ordering::Less => "더 큰 수입니다",
        Ordering::Greater => "더 작은 수입니다",
        Ordering::Equal => "맞았습니다",
    }
}

fn main() {
    println!("{:?} {:?} {:?}", 3.cmp(&7), 7.cmp(&7), 9.cmp(&7));
    for guess in [3, 9, 7] {
        println!("{guess}: {}", hint(guess, 7));
    }
    // 문자열도 튜플도 같은 메서드로 견준다
    println!("{:?}", "apple".cmp("banana"));
    println!("{:?}", (1, "b").cmp(&(1, "a")));
    // 뒤집기, 그리고 어느 변형인지 묻는 메서드
    let o = 3.cmp(&7);
    println!("{:?} {} {}", o.reverse(), o.is_lt(), o.is_ge());
}
