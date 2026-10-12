use std::rc::Rc;

// Send 인 값만 받는다. 받아서 하는 일은 없다.
fn need_send<T: Send>(_: T) {}

async fn step() {}

async fn job() -> usize {
    let shared = Rc::new(5);
    let n = *shared;
    step().await;
    n
}

fn main() {
    need_send(job());
    println!("컴파일됐다");
}
//@ expect: error
