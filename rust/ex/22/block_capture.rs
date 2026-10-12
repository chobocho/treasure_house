use std::pin::pin;
use std::task::{Context, Waker};

fn main() {
    let mut cx = Context::from_waker(Waker::noop());
    let name = String::from("ferris");
    let mut count = 1;

    // 읽기만 하는 블록: name 을 빌린다.
    let borrowed = async {
        println!("빌린 블록이 돈다: {name}");
        name.len()
    };
    // move 를 붙인 블록: 만드는 이 자리에서 count 를 가져간다.
    let owned = async move {
        println!("가져간 블록이 돈다: count = {count}");
        count + 100
    };

    count += 1;
    println!("두 블록을 만든 뒤: {name}, count = {count}");

    let mut borrowed = pin!(borrowed);
    println!("{:?}", borrowed.as_mut().poll(&mut cx));
    let mut owned = pin!(owned);
    println!("{:?}", owned.as_mut().poll(&mut cx));
}
