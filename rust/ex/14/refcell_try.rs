use std::cell::RefCell;

fn main() {
    let cell = RefCell::new(5);

    let reader = cell.borrow();
    // try_ 로 시작하는 쪽은 패닉 대신 Result 를 돌려준다.
    println!("{}", cell.try_borrow_mut().is_err());
    drop(reader); // 읽는 빌림을 끝낸다
    println!("{}", cell.try_borrow_mut().is_ok());
}
