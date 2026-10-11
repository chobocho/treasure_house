use std::cell::RefCell;

fn main() {
    let cell = RefCell::new(vec![1, 2, 3]);

    let reader = cell.borrow(); // 불변 빌림이 살아 있는 동안
    let mut writer = cell.borrow_mut(); // 가변 빌림을 또 얻으려 한다
    writer.push(4);
    println!("{:?}", reader);
}
//@ exit: 101
