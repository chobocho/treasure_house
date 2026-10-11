use std::cell::RefCell;

fn main() {
    let log = RefCell::new(Vec::new()); // mut 가 아니다

    log.borrow_mut().push("시작"); // 그런데 고칠 수 있다
    log.borrow_mut().push("끝");

    println!("{:?}", log.borrow());
    println!("{}", log.borrow().len());
}
