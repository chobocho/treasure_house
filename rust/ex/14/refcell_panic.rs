use std::cell::RefCell;

fn main() {
    let cell = RefCell::new(vec![1, 2, 3]);

    let reader = cell.borrow(); // 읽는 빌림이 살아 있는 동안
    let mut writer = cell.borrow_mut(); // 쓰는 빌림을 또 얻으려 한다
    writer.push(4);
    println!("{:?}", reader);
}
//@ exit: 101
