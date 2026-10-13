use std::cell::RefCell;

fn main() {
    let cell = RefCell::new(vec![1, 2, 3]);

    let mut writer = cell.borrow_mut();
    writer.push(4);
    // writer 는 이 뒤로 쓰지 않는다
    drop(writer);
    println!("{:?}", cell.borrow());
}
