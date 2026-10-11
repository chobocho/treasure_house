use std::sync::Mutex;

fn main() {
    let counter = Mutex::new(0);
    {
        // lock 은 "열쇠" 를 돌려준다. 열쇠를 통해서만 속의 값에 닿는다.
        let mut guard = counter.lock().unwrap();
        *guard += 1;
    } // 열쇠가 사라지며 잠금이 풀린다

    *counter.lock().unwrap() += 10;
    println!("{:?}", counter.lock().unwrap());
}
